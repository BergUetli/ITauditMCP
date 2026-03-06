"""
Audit Pipeline - Orchestrates full audit analysis: Input → Gate → Retrieval → LLM → Gate → Result.
Each public method represents an MCP tool for AI agents to call.
"""

from dataclasses import dataclass, field
from typing import Optional
from knowledge.retriever import KnowledgeRetriever, ControlContext
from knowledge.store import KnowledgeStore
from knowledge.models import UsageLog
from quality.input_gate import InputGate, InputValidation
from quality.output_gate import OutputGate, OutputValidation
from llm.engine import LLMEngine, EngineResult
from audit.prompts import (
    PROCESS_PARSER_PROMPT,
    RISK_IDENTIFIER_PROMPT,
    CONTROL_IDENTIFIER_PROMPT,
    DESIGN_ASSESSOR_PROMPT,
    EVIDENCE_ASSESSOR_PROMPT,
    FINDING_GENERATOR_PROMPT,
    FRAMEWORK_MAPPER_PROMPT,
)
import time


@dataclass
class AuditResult:
    """Final result of any audit analysis with content, confidence, and metadata."""
    content: str
    confidence_score: float = 0.0
    input_validation: Optional[InputValidation] = None
    output_validation: Optional[OutputValidation] = None
    frameworks_used: list[str] = field(default_factory=list)
    controls_referenced: list[str] = field(default_factory=list)
    industry: Optional[str] = None
    response_time_ms: int = 0
    warnings: list[str] = field(default_factory=list)


class AuditPipeline:
    """Main entry point for all audit analysis. Coordinates all pipeline components."""

    def __init__(
        self,
        store: Optional[KnowledgeStore] = None,
        retriever: Optional[KnowledgeRetriever] = None,
        engine: Optional[LLMEngine] = None,
        input_gate: Optional[InputGate] = None,
        output_gate: Optional[OutputGate] = None,
    ):
        """Initializes pipeline with optional dependency overrides for testing."""
        self.store = store or KnowledgeStore()
        self.retriever = retriever or KnowledgeRetriever(self.store)
        self.engine = engine or LLMEngine()
        self.input_gate = input_gate or InputGate()
        self.output_gate = output_gate or OutputGate(self.store)

    async def parse_process(
        self, process_text: str
    ) -> AuditResult:
        """Parses process description into structured steps, actors, and handoffs."""
        start = time.time()

        # 1. Input Gate
        validation = self.input_gate.validate(process_text)

        # 2. No knowledge retrieval needed for process parsing
        #    (we're just structuring the input, not looking up controls yet)

        # 3. LLM Engine (single call, no reviewer needed for parsing)
        llm_response = await self.engine.analyze_single(
            context="(No framework context needed for process parsing)",
            question=process_text,
            system_prompt=PROCESS_PARSER_PROMPT,
        )

        # 4. Output Gate (light validation — no control IDs expected)
        output_val = OutputValidation(
            is_valid=True,
            validated_output=llm_response.content,
            confidence_score=0.8,  # Process parsing is straightforward
        )

        elapsed = int((time.time() - start) * 1000)

        return AuditResult(
            content=llm_response.content,
            confidence_score=output_val.confidence_score,
            input_validation=validation,
            output_validation=output_val,
            response_time_ms=elapsed,
        )

    async def identify_risks(
        self,
        process_text: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> AuditResult:
        """Identifies risks in a process with framework mappings. Core value proposition."""
        start = time.time()

        # 1. Input Gate - validate and extract metadata
        validation = self.input_gate.validate(process_text)

        # Use detected framework/industry if not explicitly provided
        if not framework and validation.detected_frameworks:
            framework = validation.detected_frameworks[0]
        if not industry and validation.detected_industry:
            industry = validation.detected_industry

        # 2. Knowledge Retrieval - find relevant controls
        context_parts = []
        controls_referenced = []

        if framework:
            # Get controls related to the process text
            contexts = self.retriever.get_controls_for_risk_area(
                search_text=process_text[:200],  # First 200 chars as search
                framework_slug=framework,
                industry=industry,
            )
            for ctx in contexts:
                context_parts.append(ctx.to_llm_context())
                controls_referenced.append(ctx.control.control_id_code)

        # If no specific controls found, provide framework overview
        if not context_parts:
            context_parts.append(
                "No specific controls matched in the knowledge base. "
                "Use your general knowledge of IT audit frameworks, "
                "but clearly indicate when you're not referencing a specific "
                "control ID from the knowledge base."
            )

        full_context = "\n\n---\n\n".join(context_parts)

        # 3. LLM Engine - analyst + reviewer
        engine_result = await self.engine.analyze(
            context=full_context,
            question=f"Identify all significant risks in this process:\n\n{process_text}",
            analyst_system_prompt=RISK_IDENTIFIER_PROMPT,
        )

        # 4. Output Gate - validate the LLM's response
        output_val = self.output_gate.validate(engine_result.final_output)

        # 5. Log usage for the learning loop
        elapsed = int((time.time() - start) * 1000)
        self.store.log_usage(UsageLog(
            tool_name="identify_risks",
            input_summary=process_text[:200],
            controls_retrieved=controls_referenced,
            frameworks_referenced=[framework] if framework else [],
            industry=industry or "",
            confidence_score=output_val.confidence_score,
            response_time_ms=elapsed,
        ))

        # Combine all warnings
        all_warnings = validation.warnings + output_val.warnings

        return AuditResult(
            content=output_val.validated_output,
            confidence_score=output_val.confidence_score,
            input_validation=validation,
            output_validation=output_val,
            frameworks_used=[framework] if framework else [],
            controls_referenced=controls_referenced,
            industry=industry,
            response_time_ms=elapsed,
            warnings=all_warnings,
        )

    async def identify_expected_controls(
        self,
        risks_text: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> AuditResult:
        """Determines what controls should exist to mitigate identified risks."""
        start = time.time()
        validation = self.input_gate.validate(risks_text)

        if not framework and validation.detected_frameworks:
            framework = validation.detected_frameworks[0]
        if not industry and validation.detected_industry:
            industry = validation.detected_industry

        # Retrieve relevant framework controls
        context_parts = []
        if framework:
            contexts = self.retriever.get_controls_for_risk_area(
                search_text=risks_text[:200],
                framework_slug=framework,
                industry=industry,
            )
            for ctx in contexts:
                context_parts.append(ctx.to_llm_context())

        full_context = "\n\n---\n\n".join(context_parts) if context_parts else ""

        engine_result = await self.engine.analyze(
            context=full_context,
            question=f"Based on these risks, identify expected controls:\n\n{risks_text}",
            analyst_system_prompt=CONTROL_IDENTIFIER_PROMPT,
        )

        output_val = self.output_gate.validate(engine_result.final_output)
        elapsed = int((time.time() - start) * 1000)

        return AuditResult(
            content=output_val.validated_output,
            confidence_score=output_val.confidence_score,
            input_validation=validation,
            output_validation=output_val,
            frameworks_used=[framework] if framework else [],
            industry=industry,
            response_time_ms=elapsed,
            warnings=validation.warnings + output_val.warnings,
        )

    async def assess_design_effectiveness(
        self,
        control_description: str,
        risk_description: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> AuditResult:
        """Assesses whether a control is properly designed to mitigate a risk."""
        start = time.time()
        validation = self.input_gate.validate(control_description)

        context_parts = []
        if framework:
            contexts = self.retriever.get_controls_for_risk_area(
                search_text=control_description[:200],
                framework_slug=framework,
                industry=industry,
            )
            for ctx in contexts:
                context_parts.append(ctx.to_llm_context())

        full_context = "\n\n---\n\n".join(context_parts) if context_parts else ""

        question = (
            f"Assess the design effectiveness of this control:\n\n"
            f"CONTROL: {control_description}\n\n"
            f"RISK IT SHOULD MITIGATE: {risk_description}"
        )

        engine_result = await self.engine.analyze(
            context=full_context,
            question=question,
            analyst_system_prompt=DESIGN_ASSESSOR_PROMPT,
        )

        output_val = self.output_gate.validate(engine_result.final_output)
        elapsed = int((time.time() - start) * 1000)

        return AuditResult(
            content=output_val.validated_output,
            confidence_score=output_val.confidence_score,
            input_validation=validation,
            output_validation=output_val,
            response_time_ms=elapsed,
            warnings=validation.warnings + output_val.warnings,
        )

    async def assess_evidence(
        self,
        control_description: str,
        evidence_description: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> AuditResult:
        """Assesses operating effectiveness of a control based on provided evidence."""
        start = time.time()
        validation = self.input_gate.validate(evidence_description)

        context_parts = []
        if framework:
            contexts = self.retriever.get_controls_for_risk_area(
                search_text=control_description[:200],
                framework_slug=framework,
                industry=industry,
            )
            for ctx in contexts:
                context_parts.append(ctx.to_llm_context())

        full_context = "\n\n---\n\n".join(context_parts) if context_parts else ""

        question = (
            f"Assess operating effectiveness based on this evidence:\n\n"
            f"CONTROL: {control_description}\n\n"
            f"EVIDENCE PROVIDED: {evidence_description}"
        )

        engine_result = await self.engine.analyze(
            context=full_context,
            question=question,
            analyst_system_prompt=EVIDENCE_ASSESSOR_PROMPT,
        )

        output_val = self.output_gate.validate(engine_result.final_output)
        elapsed = int((time.time() - start) * 1000)

        return AuditResult(
            content=output_val.validated_output,
            confidence_score=output_val.confidence_score,
            response_time_ms=elapsed,
            warnings=validation.warnings + output_val.warnings,
        )

    async def generate_finding(
        self,
        condition: str,
        criteria: Optional[str] = None,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> AuditResult:
        """Generates a complete audit finding with all 5 components."""
        start = time.time()
        validation = self.input_gate.validate(condition)

        context_parts = []
        if framework:
            contexts = self.retriever.get_controls_for_risk_area(
                search_text=condition[:200],
                framework_slug=framework,
                industry=industry,
            )
            for ctx in contexts:
                context_parts.append(ctx.to_llm_context())

        full_context = "\n\n---\n\n".join(context_parts) if context_parts else ""

        question = f"Generate a complete audit finding:\n\nCONDITION: {condition}"
        if criteria:
            question += f"\n\nCRITERIA: {criteria}"

        engine_result = await self.engine.analyze(
            context=full_context,
            question=question,
            analyst_system_prompt=FINDING_GENERATOR_PROMPT,
        )

        output_val = self.output_gate.validate(engine_result.final_output)
        elapsed = int((time.time() - start) * 1000)

        return AuditResult(
            content=output_val.validated_output,
            confidence_score=output_val.confidence_score,
            response_time_ms=elapsed,
            warnings=validation.warnings + output_val.warnings,
        )

    async def map_frameworks(
        self,
        control_id_code: str,
        source_framework: str,
        target_frameworks: Optional[list[str]] = None,
    ) -> AuditResult:
        """Maps a control from one framework to equivalent controls in other frameworks."""
        start = time.time()

        # Get full context for this control
        context = self.retriever.get_full_control_context(
            framework_slug=source_framework,
            control_id_code=control_id_code,
        )

        if context:
            full_context = context.to_llm_context()
        else:
            full_context = f"Control {control_id_code} not found in {source_framework}."

        targets = target_frameworks or [
            "cobit_2019", "iso_27001_2022", "nist_csf_2", "ffiec_it", "soc2_tsc"
        ]
        targets = [t for t in targets if t != source_framework]

        question = (
            f"Map control {control_id_code} from {source_framework} "
            f"to the following frameworks: {', '.join(targets)}"
        )

        engine_result = await self.engine.analyze(
            context=full_context,
            question=question,
            analyst_system_prompt=FRAMEWORK_MAPPER_PROMPT,
        )

        output_val = self.output_gate.validate(engine_result.final_output)
        elapsed = int((time.time() - start) * 1000)

        return AuditResult(
            content=output_val.validated_output,
            confidence_score=output_val.confidence_score,
            frameworks_used=[source_framework] + targets,
            response_time_ms=elapsed,
        )
