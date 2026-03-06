"""Assembles full audit context from multiple knowledge store lookups.
Combines controls, mappings, overlays, evidence, and expert interpretations into rich LLM context."""

from dataclasses import dataclass, field
from knowledge.store import KnowledgeStore
from knowledge.models import (
    Control, ControlMapping, IndustryOverlay,
    EvidenceRequirement, Interpretation, Framework,
    AuditProcess, ProcessPhase, Risk, RiskControlMapping,
    TestingProcedure
)
from typing import Optional


@dataclass
class ControlContext:
    """Complete control information assembled for LLM reasoning."""
    control: Control
    framework: Optional[Framework] = None

    mappings: list[ControlMapping] = field(default_factory=list)
    mapped_controls: list[Control] = field(default_factory=list)
    overlays: list[IndustryOverlay] = field(default_factory=list)
    evidence_requirements: list[EvidenceRequirement] = field(default_factory=list)
    interpretations: list[Interpretation] = field(default_factory=list)

    confidence_score: float = 0.0

    def to_llm_context(self) -> str:
        """Format context as structured markdown for LLM injection."""
        parts = []

        parts.append(f"## Control: {self.control.control_id_code}")
        parts.append(f"**Framework:** {self.framework.name if self.framework else 'Unknown'}")
        parts.append(f"**Title:** {self.control.title}")
        if self.control.description:
            parts.append(f"**Description:** {self.control.description}")
        if self.control.objective:
            parts.append(f"**Objective:** {self.control.objective}")
        if self.control.testing_procedure:
            parts.append(f"**Testing Procedure:** {self.control.testing_procedure}")
        parts.append(f"**Type:** {self.control.control_type}")
        parts.append(f"**Automation:** {self.control.automation_level}")

        if self.mapped_controls:
            parts.append("\n## Cross-Framework Mappings")
            for mapping, mapped_ctrl in zip(self.mappings, self.mapped_controls):
                strength = mapping.mapping_strength
                if hasattr(strength, 'value'):
                    strength = strength.value
                parts.append(
                    f"- **{mapped_ctrl.control_id_code}** ({mapped_ctrl.title}) "
                    f"[{strength} match, confidence: {mapping.confidence_score}]"
                )
                if mapping.rationale:
                    parts.append(f"  Rationale: {mapping.rationale}")

        if self.overlays:
            parts.append("\n## Industry-Specific Requirements")
            for overlay in self.overlays:
                parts.append(
                    f"- **{overlay.regulatory_body}** ({overlay.industry}): "
                    f"{overlay.description}"
                )
                if overlay.regulation_ref:
                    parts.append(f"  Reference: {overlay.regulation_ref}")

        if self.evidence_requirements:
            parts.append("\n## Evidence Requirements")
            for ev in self.evidence_requirements:
                mandatory = "MANDATORY" if ev.is_mandatory else "Optional"
                parts.append(f"- [{mandatory}] {ev.description}")
                if ev.sampling_guidance:
                    parts.append(f"  Sampling: {ev.sampling_guidance}")
                if ev.typical_sources:
                    parts.append(f"  Common sources: {', '.join(ev.typical_sources)}")

        if self.interpretations:
            parts.append("\n## Expert Insights")
            for interp in self.interpretations:
                interp_type = interp.interpretation_type
                if hasattr(interp_type, 'value'):
                    interp_type = interp_type.value
                parts.append(
                    f"- **[{interp_type}]** {interp.content} "
                    f"(confidence: {interp.confidence})"
                )

        parts.append(f"\n**Overall Context Confidence: {self.confidence_score:.2f}**")

        return "\n".join(parts)


@dataclass
class RiskDetail:
    """A sub-risk with its control, test steps, and evidence assembled."""
    risk: Risk
    control_mapping: Optional[RiskControlMapping] = None
    testing_procedures: list[TestingProcedure] = field(default_factory=list)
    evidence_requirements: list[EvidenceRequirement] = field(default_factory=list)


@dataclass
class PhaseContext:
    """All risks and controls for a single phase of an audit process."""
    phase: ProcessPhase
    parent_risks: list[Risk] = field(default_factory=list)
    risk_details: list[RiskDetail] = field(default_factory=list)


@dataclass
class ProcessContext:
    """Complete audit context for a process, assembled for LLM reasoning."""
    process: AuditProcess
    phases: list[PhaseContext] = field(default_factory=list)

    def to_llm_context(self) -> str:
        """Format as structured markdown for LLM injection."""
        parts = []
        parts.append(f"# Audit Process: {self.process.code} — {self.process.name}")
        if self.process.description:
            parts.append(f"{self.process.description}")
        parts.append(f"**Category:** {self.process.category} | **Banking Priority:** {self.process.banking_priority}")
        parts.append("")

        for pc in self.phases:
            parts.append(f"## Phase {pc.phase.phase_number}: {pc.phase.name}")
            if pc.phase.description:
                parts.append(f"{pc.phase.description}")
            parts.append("")

            for rd in pc.risk_details:
                parts.append(f"### {rd.risk.risk_code}: {rd.risk.description}")
                if rd.control_mapping:
                    cm = rd.control_mapping
                    parts.append(f"**Expected Control ({cm.control_type}):** {cm.control_description}")
                    if cm.framework_refs:
                        parts.append(f"**Framework Refs:** {cm.framework_refs}")

                if rd.testing_procedures:
                    parts.append("**Testing Procedures:**")
                    for tp in rd.testing_procedures:
                        parts.append(f"  {tp.step_number}. {tp.procedure}")

                if rd.evidence_requirements:
                    parts.append("**Evidence Required:**")
                    for ev in rd.evidence_requirements:
                        mandatory = "MANDATORY" if ev.is_mandatory else "Optional"
                        parts.append(f"  - [{mandatory}] {ev.description}")

                parts.append("")

        return "\n".join(parts)

    def to_summary(self) -> str:
        """Short summary for listing — no test steps or evidence."""
        parts = []
        parts.append(f"**{self.process.code} — {self.process.name}**")
        parts.append(f"Category: {self.process.category} | Priority: {self.process.banking_priority}")
        total_risks = sum(len(pc.risk_details) for pc in self.phases)
        parts.append(f"Phases: {len(self.phases)} | Sub-risks: {total_risks}")
        for pc in self.phases:
            parts.append(f"  {pc.phase.phase_number}. {pc.phase.name} ({len(pc.risk_details)} risks)")
        return "\n".join(parts)


class KnowledgeRetriever:
    """Main interface for assembling full audit context for controls and frameworks."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self.store = store or KnowledgeStore()

    def get_full_control_context(
        self,
        framework_slug: str,
        control_id_code: str,
        industry: Optional[str] = None
    ) -> Optional[ControlContext]:
        """Retrieve complete control context including mappings, overlays, evidence, and interpretations."""
        control = self.store.get_control_by_code(framework_slug, control_id_code)
        if not control or not control.id:
            return None

        framework = self.store.get_framework_by_slug(framework_slug)

        mappings = self.store.get_mappings_for_control(control.id)
        mapped_controls = []
        for mapping in mappings:
            # Determine which control ID is the "other" one in the mapping
            other_id = (
                mapping.target_control_id
                if mapping.source_control_id == control.id
                else mapping.source_control_id
            )
            other_result = (
                self.store.client.table("controls")
                .select("*")
                .eq("id", other_id)
                .execute()
            )
            if other_result.data:
                mapped_controls.append(Control(**other_result.data[0]))

        overlays = []
        industry_overlay_id = None
        if industry:
            overlays = self.store.get_overlays_for_control(control.id, industry)
            if overlays:
                industry_overlay_id = overlays[0].id

        evidence = self.store.get_evidence_for_control(
            control.id, industry_overlay_id
        )

        interpretations = self.store.get_interpretations_for_control(
            control.id, industry_overlay_id
        )

        # Average confidence from mappings and interpretations
        confidence_scores = []
        for m in mappings:
            if m.confidence_score is not None:
                confidence_scores.append(m.confidence_score)
        for i in interpretations:
            if i.confidence is not None:
                confidence_scores.append(i.confidence)
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.5
        )

        # Track interpretation usage for learning
        for interp in interpretations:
            if interp.id:
                self.store.increment_interpretation_usage(interp.id)

        return ControlContext(
            control=control,
            framework=framework,
            mappings=mappings,
            mapped_controls=mapped_controls,
            overlays=overlays,
            evidence_requirements=evidence,
            interpretations=interpretations,
            confidence_score=overall_confidence
        )

    def get_controls_for_risk_area(
        self,
        search_text: str,
        framework_slug: Optional[str] = None,
        industry: Optional[str] = None
    ) -> list[ControlContext]:
        """Find relevant controls for a risk or process area with full context."""
        controls = self.store.search_controls_by_text(search_text)

        if framework_slug:
            fw = self.store.get_framework_by_slug(framework_slug)
            if fw:
                controls = [c for c in controls if c.framework_id == fw.id]

        # Build context for top 10 matches without re-fetching control data
        contexts = []
        for control in controls[:10]:
            if control.id:
                mappings = self.store.get_mappings_for_control(control.id)

                overlays = []
                industry_overlay_id = None
                if industry:
                    overlays = self.store.get_overlays_for_control(
                        control.id, industry
                    )
                    if overlays:
                        industry_overlay_id = overlays[0].id

                evidence = self.store.get_evidence_for_control(
                    control.id, industry_overlay_id
                )
                interpretations = self.store.get_interpretations_for_control(
                    control.id, industry_overlay_id
                )

                contexts.append(ControlContext(
                    control=control,
                    mappings=mappings,
                    overlays=overlays,
                    evidence_requirements=evidence,
                    interpretations=interpretations
                ))

        return contexts

    # ================================================================
    # PROCESS-CENTRIC RETRIEVAL
    # ================================================================

    def get_process_context(
        self, process_code: str, phase_number: Optional[int] = None
    ) -> Optional[ProcessContext]:
        """Retrieve full audit context for a process (or a single phase)."""
        process = self.store.get_audit_process_by_code(process_code)
        if not process or not process.id:
            return None

        all_phases = self.store.get_phases_for_process(process.id)
        if phase_number is not None:
            all_phases = [p for p in all_phases if p.phase_number == phase_number]

        phase_contexts = []
        for phase in all_phases:
            if not phase.id:
                continue

            # Get all risks for this phase
            all_risks = self.store.get_risks_for_process(process.id, phase.id)
            parent_risks = [r for r in all_risks if r.risk_level == 1]
            sub_risks = [r for r in all_risks if r.risk_level == 2]

            # Build detail for each sub-risk
            risk_details = []
            for sr in sub_risks:
                if not sr.id:
                    continue
                mapping = self.store.get_control_mapping_for_risk(sr.id)
                test_procs = []
                evidence = []
                if mapping and mapping.id:
                    test_procs = self.store.get_testing_procedures(mapping.id)
                    evidence = self.store.get_evidence_for_mapping(mapping.id)

                risk_details.append(RiskDetail(
                    risk=sr,
                    control_mapping=mapping,
                    testing_procedures=test_procs,
                    evidence_requirements=evidence,
                ))

            phase_contexts.append(PhaseContext(
                phase=phase,
                parent_risks=parent_risks,
                risk_details=risk_details,
            ))

        return ProcessContext(process=process, phases=phase_contexts)

    def list_populated_processes(self) -> list[AuditProcess]:
        """Return only processes that have risks seeded (not empty shells)."""
        all_processes = self.store.get_all_audit_processes()
        populated = []
        for p in all_processes:
            if p.id:
                risks = self.store.get_parent_risks_for_process(p.id)
                if risks:
                    populated.append(p)
        return populated
