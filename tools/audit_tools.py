"""
MCP tool wrappers for the audit pipeline.
Thin layer that AI agents call, with real logic in audit/pipeline.py.
"""

from fastmcp import FastMCP
from typing import Optional
from audit.pipeline import AuditPipeline
from knowledge.retriever import KnowledgeRetriever


# Single pipeline instance shared across all tools
# Created when tools are registered (server startup)
_pipeline: Optional[AuditPipeline] = None


def register_tools(mcp: FastMCP):
    """Register all audit tools at server startup."""
    global _pipeline
    _pipeline = AuditPipeline()

    # ================================================================
    # PROCESS TOOLS
    # ================================================================

    @mcp.tool()
    async def parse_process(process_description: str) -> str:
        """Break a business process description into numbered steps."""
        result = await _pipeline.parse_process(process_description)
        return _format_result(result)

    # ================================================================
    # RISK TOOLS
    # ================================================================

    @mcp.tool()
    async def identify_risks(
        process_text: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> str:
        """Identify risks in a business process against audit frameworks."""
        result = await _pipeline.identify_risks(process_text, framework, industry)
        return _format_result(result)

    # ================================================================
    # CONTROL TOOLS
    # ================================================================

    @mcp.tool()
    async def identify_expected_controls(
        risks_text: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> str:
        """Determine what controls should exist to mitigate identified risks."""
        result = await _pipeline.identify_expected_controls(
            risks_text, framework, industry
        )
        return _format_result(result)

    @mcp.tool()
    async def assess_design_effectiveness(
        control_description: str,
        risk_description: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> str:
        """Check if a control is properly designed to prevent a risk."""
        result = await _pipeline.assess_design_effectiveness(
            control_description, risk_description, framework, industry
        )
        return _format_result(result)

    @mcp.tool()
    async def assess_evidence(
        control_description: str,
        evidence_description: str,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> str:
        """Check if evidence shows a control is actually working."""
        result = await _pipeline.assess_evidence(
            control_description, evidence_description, framework, industry
        )
        return _format_result(result)

    # ================================================================
    # FINDING TOOLS
    # ================================================================

    @mcp.tool()
    async def generate_finding(
        condition: str,
        criteria: Optional[str] = None,
        framework: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> str:
        """Create a complete audit finding with condition, criteria, and recommendations."""
        result = await _pipeline.generate_finding(
            condition, criteria, framework, industry
        )
        return _format_result(result)

    # ================================================================
    # KNOWLEDGE BASE TOOLS (Process-Centric)
    # ================================================================

    _retriever = KnowledgeRetriever()

    @mcp.tool()
    async def list_audit_processes(category: Optional[str] = None) -> str:
        """List available IT audit processes. Optionally filter by category (Security, Operations, Governance, Data, Development, Infrastructure)."""
        if category:
            processes = _retriever.store.get_audit_processes_by_category(category)
        else:
            processes = _retriever.list_populated_processes()

        if not processes:
            return "No audit processes found."

        lines = ["# Available IT Audit Processes\n"]
        for p in processes:
            lines.append(f"- **{p.code}** — {p.name} [{p.banking_priority}] ({p.category})")
        lines.append(f"\n*{len(processes)} processes listed. Use get_process_detail for full context.*")
        return "\n".join(lines)

    @mcp.tool()
    async def get_process_detail(
        process_code: str,
        phase_number: Optional[int] = None
    ) -> str:
        """Get full audit context for a process (risks, controls, test steps, evidence). Optionally filter to a single phase by number."""
        ctx = _retriever.get_process_context(process_code, phase_number)
        if not ctx:
            return f"Process '{process_code}' not found or has no data."
        return ctx.to_llm_context()

    @mcp.tool()
    async def get_process_summary(process_code: str) -> str:
        """Get a short summary of a process — phases and risk counts, no detail."""
        ctx = _retriever.get_process_context(process_code)
        if not ctx:
            return f"Process '{process_code}' not found or has no data."
        return ctx.to_summary()

    @mcp.tool()
    async def get_risks_for_process(
        process_code: str,
        phase_number: Optional[int] = None
    ) -> str:
        """List all risks for a process, grouped by phase. Optionally filter by phase number."""
        ctx = _retriever.get_process_context(process_code, phase_number)
        if not ctx:
            return f"Process '{process_code}' not found or has no data."

        lines = [f"# Risks: {ctx.process.code} — {ctx.process.name}\n"]
        for pc in ctx.phases:
            lines.append(f"## Phase {pc.phase.phase_number}: {pc.phase.name}")
            for pr in pc.parent_risks:
                lines.append(f"\n**{pr.risk_code}: {pr.description}**")
                # Find sub-risks under this parent
                for rd in pc.risk_details:
                    if rd.risk.parent_risk_id == pr.id:
                        lines.append(f"  - {rd.risk.risk_code}: {rd.risk.description}")
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    async def get_testing_procedures_for_risk(risk_code: str, process_code: str) -> str:
        """Get detailed testing procedures and evidence for a specific sub-risk code (e.g., 'CM1.1.1') within a process."""
        ctx = _retriever.get_process_context(process_code)
        if not ctx:
            return f"Process '{process_code}' not found."

        for pc in ctx.phases:
            for rd in pc.risk_details:
                if rd.risk.risk_code == risk_code:
                    lines = [f"# {rd.risk.risk_code}: {rd.risk.description}\n"]
                    if rd.control_mapping:
                        cm = rd.control_mapping
                        lines.append(f"**Expected Control:** {cm.control_description}")
                        lines.append(f"**Control Type:** {cm.control_type}")
                        if cm.framework_refs:
                            lines.append(f"**Framework Refs:** {cm.framework_refs}")

                    if rd.testing_procedures:
                        lines.append("\n**Testing Procedures:**")
                        for tp in rd.testing_procedures:
                            lines.append(f"{tp.step_number}. {tp.procedure}")

                    if rd.evidence_requirements:
                        lines.append("\n**Evidence Required:**")
                        for ev in rd.evidence_requirements:
                            mandatory = "MANDATORY" if ev.is_mandatory else "Optional"
                            lines.append(f"- [{mandatory}] {ev.description}")

                    return "\n".join(lines)

        return f"Risk code '{risk_code}' not found in process '{process_code}'."

    # ================================================================
    # SCOPE AND CONTENT TOOLS (Entry Point B — Natural Language)
    # ================================================================

    @mcp.tool()
    async def scope_audit(process_description: str, scope_decisions: str) -> str:
        """Match a plain-English description of the business process being audited to
        the relevant audit programme(s), filtered by agreed scope.

        Call this when the auditor describes a process in natural language and you need
        to figure out which audit programmes apply. Returns matched programmes with
        summaries and scope boundaries.

        Args:
            process_description: What the client described about the process to audit.
                Example: "We want to audit how the bank handles employee joiners and
                leavers and their access to systems."
            scope_decisions: What was agreed about scope — focus areas, exclusions,
                depth, timeframe. Example: "Focus on privileged accounts only,
                exclude general user access, cover last 12 months."
        """
        result = await _pipeline.scope_audit(process_description, scope_decisions)
        return _format_result(result)

    @mcp.tool()
    async def get_audit_content(
        process_code: str, risk_focus: Optional[str] = None
    ) -> str:
        """Retrieve the full audit programme for a known process code.

        Call scope_audit first to identify the right process code(s). Then call
        this tool for each process code to get the detailed risks, controls,
        testing procedures, and evidence requirements.

        Args:
            process_code: Internal process code (e.g., 'P04', 'P07').
            risk_focus: Optional — filter to specific risk areas within the
                programme. Example: "privileged accounts" or "deprovisioning".
        """
        ctx = _retriever.get_process_context(process_code)
        if not ctx:
            return f"Process '{process_code}' not found or has no data."

        # No filter — return the full programme
        if not risk_focus:
            return ctx.to_llm_context()

        # Filter output to phases/risks that mention the focus term
        focus_lower = risk_focus.lower()
        parts = [f"# Audit Programme: {ctx.process.name}"]
        parts.append(f"**Focus area:** {risk_focus}\n")

        for pc in ctx.phases:
            # Check which risk details in this phase match the focus
            matching = []
            for rd in pc.risk_details:
                searchable = rd.risk.description.lower()
                if rd.control_mapping:
                    searchable += " " + rd.control_mapping.control_description.lower()
                if focus_lower in searchable:
                    matching.append(rd)

            # Also include the phase if its name matches the focus
            phase_matches = focus_lower in pc.phase.name.lower()
            if not matching and not phase_matches:
                continue

            parts.append(f"## Phase {pc.phase.phase_number}: {pc.phase.name}")
            if pc.phase.description:
                parts.append(pc.phase.description)
            parts.append("")

            # Show matching risks, or all risks if only the phase name matched
            details_to_show = matching if matching else pc.risk_details
            for rd in details_to_show:
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

        # If nothing matched the filter, return full context with a note
        if len(parts) <= 2:
            return (
                f"**No risks matched '{risk_focus}'.** Showing full programme:\n\n"
                + ctx.to_llm_context()
            )

        return "\n".join(parts)

    # ================================================================
    # FRAMEWORK TOOLS
    # ================================================================

    @mcp.tool()
    async def map_frameworks(
        control_id: str,
        source_framework: str,
        target_frameworks: Optional[str] = None,
    ) -> str:
        """Show how a control in one framework relates to other frameworks."""
        targets = None
        if target_frameworks:
            targets = [t.strip() for t in target_frameworks.split(",")]

        result = await _pipeline.map_frameworks(
            control_id, source_framework, targets
        )
        return _format_result(result)


def _format_result(result) -> str:
    """Format an audit result with content and metadata."""
    parts = [result.content]

    parts.append(f"\n\n---\n**Confidence Score:** {result.confidence_score:.2f}")

    if result.frameworks_used:
        parts.append(f"**Frameworks Used:** {', '.join(result.frameworks_used)}")
    if result.industry:
        parts.append(f"**Industry Context:** {result.industry}")
    if result.response_time_ms:
        parts.append(f"**Response Time:** {result.response_time_ms}ms")

    if result.warnings:
        parts.append("\n**Warnings:**")
        for w in result.warnings:
            parts.append(f"- {w}")

    return "\n".join(parts)
