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
    PROCESS_RESOLVER_PROMPT,
)
import json
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

    async def resolve_process(self, description: str) -> list[dict]:
        """Match a plain-English process description to audit programme codes.

        Two-step resolution:
        Step A — Keyword matching via retriever.find_process_candidates().
                 Searches process names, phase names, risk descriptions, and
                 control descriptions for word overlap.
        Step B — LLM reasoning to confirm/adjust matches. Gets the keyword
                 scores as hints plus the full list of available programmes
                 so it can catch matches that keywords missed.

        Args:
            description: Free-text description of the process being audited.

        Returns:
            List of dicts with process_code, relevance, and reasoning.
            Example: [{"process_code": "P07", "relevance": "high", "reasoning": "..."}]
        """
        # Step A: keyword candidates from the knowledge layer
        candidates = self.retriever.find_process_candidates(description)

        # Build LLM context with keyword results + full programme list
        # Cache phase lookups — each process's phases are used in both sections
        phases_by_id: dict[str, list] = {}
        for process, _ in candidates:
            if process.id:
                phases_by_id[process.id] = self.store.get_phases_for_process(process.id)

        context_lines = []

        # Section 1: keyword match results
        context_lines.append("# Keyword Match Candidates\n")
        has_keyword_hits = False
        for process, score in candidates:
            if score > 0:
                has_keyword_hits = True
                phase_names = ", ".join(p.name for p in phases_by_id.get(process.id, []))
                context_lines.append(
                    f"- **{process.code}** {process.name} (score: {score:.2f})\n"
                    f"  Phases: {phase_names}"
                )
        if not has_keyword_hits:
            context_lines.append("- No keyword matches found.")

        # Section 2: full list so the LLM can catch what keywords missed
        context_lines.append("\n# All Available Audit Programmes\n")
        for process, _ in candidates:
            phase_names = ", ".join(p.name for p in phases_by_id.get(process.id, []))
            context_lines.append(
                f"- **{process.code}** {process.name} ({process.category})\n"
                f"  {process.description or 'No description'}\n"
                f"  Phases: {phase_names}"
            )

        context = "\n".join(context_lines)

        # Step B: LLM decides which programmes apply
        llm_response = await self.engine.analyze_single(
            context=context,
            question=f"Match this process description to audit programmes:\n\n{description}",
            system_prompt=PROCESS_RESOLVER_PROMPT,
        )

        # Parse JSON from LLM response
        try:
            raw = llm_response.content.strip()
            # Strip markdown code fences if the LLM wraps its response
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                raw = raw.rsplit("```", 1)[0]
            result = json.loads(raw)
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, IndexError, KeyError):
            pass

        # Fallback: if LLM returned garbage, use keyword top match.
        # 0.3 = at least 30% of the description words appear in the process
        # vocabulary. Below that the match is too weak to trust without LLM.
        keyword_fallback_threshold = 0.3
        if candidates and candidates[0][1] > keyword_fallback_threshold:
            top_process, top_score = candidates[0]
            # Derive relevance from keyword score instead of hardcoding
            if top_score > 0.6:
                fallback_relevance = "high"
            elif top_score > 0.4:
                fallback_relevance = "medium"
            else:
                fallback_relevance = "low"
            return [{"process_code": top_process.code, "relevance": fallback_relevance,
                     "reasoning": f"Keyword match (score {top_score:.2f}), LLM response was unusable"}]

        return [{"process_code": "NONE", "relevance": "none",
                 "reasoning": "No matching audit programmes found"}]

    async def scope_audit(
        self, process_description: str, scope_decisions: str
    ) -> AuditResult:
        """Match a process description to audit programmes and return scoped content.

        Calls resolve_process() to identify relevant programmes, then retrieves
        a summary for each matched programme. scope_decisions is included in the
        output so the calling agent knows what's in and out of scope.

        Args:
            process_description: Plain-English description of the process being audited.
                Example: "We want to audit how the bank handles employee joiners
                and leavers and their access to systems."
            scope_decisions: Agreed scope — focus areas, exclusions, depth, timeframe.
                Example: "Focus on privileged accounts only, exclude general user
                access, cover last 12 months."

        Returns:
            AuditResult with matched programmes, their summaries, and scope boundaries.
        """
        start = time.time()

        # Step 1: resolve which programmes are relevant
        matches = await self.resolve_process(process_description)

        # Step 2: build output with summaries for each matched programme
        content_parts = []
        content_parts.append("# Audit Scope\n")
        content_parts.append(f"**Process described:** {process_description}\n")
        content_parts.append(f"**Scope decisions:** {scope_decisions}\n")
        content_parts.append("---\n")

        for match in matches:
            code = match.get("process_code", "")
            relevance = match.get("relevance", "")
            reasoning = match.get("reasoning", "")

            if code == "NONE":
                content_parts.append(
                    "No matching audit programmes found in the knowledge base.\n"
                    f"Reason: {reasoning}"
                )
                continue

            ctx = self.retriever.get_process_context(code)
            if ctx:
                content_parts.append(
                    f"## {ctx.process.name} [{relevance.upper()}]\n"
                    f"*{reasoning}*\n"
                )
                content_parts.append(ctx.to_summary())
                content_parts.append("")
            else:
                content_parts.append(
                    f"## {code} [{relevance.upper()}] — no data loaded yet\n"
                    f"*{reasoning}*\n"
                )

        # Compute confidence from the LLM's relevance ratings rather than hardcoding
        relevance_weights = {"high": 0.9, "medium": 0.7, "low": 0.5, "none": 0.2}
        relevance_scores = [
            relevance_weights.get(m.get("relevance", "none"), 0.5)
            for m in matches
        ]
        confidence = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.3

        elapsed = int((time.time() - start) * 1000)

        return AuditResult(
            content="\n".join(content_parts),
            confidence_score=confidence,
            response_time_ms=elapsed,
        )

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
