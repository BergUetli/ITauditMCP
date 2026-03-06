"""Database access layer for audit knowledge.
Handles all read/write operations to Supabase tables."""

from supabase import create_client, Client
from config.settings import settings
from knowledge.models import (
    Framework, Domain, Control, ControlMapping,
    IndustryOverlay, EvidenceRequirement, Interpretation,
    Feedback, UsageLog,
    AuditProcess, ProcessPhase, Risk, RiskControlMapping,
    TestingProcedure
)
from typing import Optional


class KnowledgeStore:
    """Database access for all audit knowledge."""

    def __init__(self):
        """Connect to Supabase and initialize both read and admin clients."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
        # Service client for admin operations (seeding data, applying corrections)
        # Only created if service key is provided
        self._admin_client: Optional[Client] = None
        if settings.supabase_service_key:
            self._admin_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )

    @property
    def admin(self) -> Client:
        """Return admin client for write operations."""
        if not self._admin_client:
            raise ValueError(
                "No SUPABASE_SERVICE_KEY configured. "
                "Admin operations require the service role key."
            )
        return self._admin_client

    # ================================================================
    # FRAMEWORKS
    # ================================================================

    def get_all_frameworks(self) -> list[Framework]:
        """Get all audit frameworks in the system."""
        result = self.client.table("frameworks").select("*").execute()
        return [Framework(**row) for row in result.data]

    def get_framework_by_slug(self, slug: str) -> Optional[Framework]:
        """Look up a framework by slug."""
        result = (
            self.client.table("frameworks")
            .select("*")
            .eq("slug", slug)
            .execute()
        )
        if result.data:
            return Framework(**result.data[0])
        return None

    def create_framework(self, framework: Framework) -> Framework:
        """Insert a new framework. Used during seeding."""
        data = framework.model_dump(exclude_none=True, exclude={"id"})
        result = self.admin.table("frameworks").insert(data).execute()
        return Framework(**result.data[0])

    # ================================================================
    # DOMAINS
    # ================================================================

    def get_domains_by_framework(self, framework_id: str) -> list[Domain]:
        """Get all domains for a framework, ordered by hierarchy and sort."""
        result = (
            self.client.table("domains")
            .select("*")
            .eq("framework_id", framework_id)
            .order("hierarchy_level")
            .order("sort_order")
            .execute()
        )
        return [Domain(**row) for row in result.data]

    def get_domain_by_code(self, framework_id: str, code: str) -> Optional[Domain]:
        """Look up a domain by code."""
        result = (
            self.client.table("domains")
            .select("*")
            .eq("framework_id", framework_id)
            .eq("code", code)
            .execute()
        )
        if result.data:
            return Domain(**result.data[0])
        return None

    def create_domain(self, domain: Domain) -> Domain:
        """Insert a new domain. Used during seeding."""
        data = domain.model_dump(exclude_none=True, exclude={"id"})
        result = self.admin.table("domains").insert(data).execute()
        return Domain(**result.data[0])

    # ================================================================
    # CONTROLS
    # ================================================================

    def get_control_by_code(
        self, framework_slug: str, control_id_code: str
    ) -> Optional[Control]:
        """Look up a specific control by framework and control ID."""
        # First get the framework ID from the slug
        fw = self.get_framework_by_slug(framework_slug)
        if not fw or not fw.id:
            return None

        result = (
            self.client.table("controls")
            .select("*")
            .eq("framework_id", fw.id)
            .eq("control_id_code", control_id_code)
            .execute()
        )
        if result.data:
            return Control(**result.data[0])
        return None

    def get_controls_by_domain(self, domain_id: str) -> list[Control]:
        """Get all controls within a domain."""
        result = (
            self.client.table("controls")
            .select("*")
            .eq("domain_id", domain_id)
            .execute()
        )
        return [Control(**row) for row in result.data]

    def get_controls_by_framework(self, framework_id: str) -> list[Control]:
        """Get all controls for an entire framework."""
        result = (
            self.client.table("controls")
            .select("*")
            .eq("framework_id", framework_id)
            .execute()
        )
        return [Control(**row) for row in result.data]

    def search_controls_by_text(self, search_text: str) -> list[Control]:
        """Search controls by text in title and description."""
        # Search in title and description using Supabase text search
        result = (
            self.client.table("controls")
            .select("*")
            .or_(
                f"title.ilike.%{search_text}%,"
                f"description.ilike.%{search_text}%"
            )
            .execute()
        )
        return [Control(**row) for row in result.data]

    def create_control(self, control: Control) -> Control:
        """Insert a new control. Used during seeding."""
        data = control.model_dump(exclude_none=True, exclude={"id"})
        # Convert enum values to strings for Supabase
        if "control_type" in data and data["control_type"]:
            data["control_type"] = data["control_type"].value if hasattr(data["control_type"], "value") else data["control_type"]
        if "automation_level" in data and data["automation_level"]:
            data["automation_level"] = data["automation_level"].value if hasattr(data["automation_level"], "value") else data["automation_level"]
        result = self.admin.table("controls").insert(data).execute()
        return Control(**result.data[0])

    # ================================================================
    # CONTROL MAPPINGS
    # ================================================================

    def get_mappings_for_control(self, control_id: str) -> list[ControlMapping]:
        """Get all mappings (both directions) for a control."""
        # Get mappings where this control is the source
        source_result = (
            self.client.table("control_mappings")
            .select("*")
            .eq("source_control_id", control_id)
            .execute()
        )
        # Get mappings where this control is the target
        target_result = (
            self.client.table("control_mappings")
            .select("*")
            .eq("target_control_id", control_id)
            .execute()
        )
        all_mappings = source_result.data + target_result.data
        return [ControlMapping(**row) for row in all_mappings]

    def create_mapping(self, mapping: ControlMapping) -> ControlMapping:
        """Insert a new control mapping. Used during seeding."""
        data = mapping.model_dump(exclude_none=True, exclude={"id"})
        if "mapping_strength" in data:
            data["mapping_strength"] = data["mapping_strength"].value if hasattr(data["mapping_strength"], "value") else data["mapping_strength"]
        if "mapping_direction" in data:
            data["mapping_direction"] = data["mapping_direction"].value if hasattr(data["mapping_direction"], "value") else data["mapping_direction"]
        result = self.admin.table("control_mappings").insert(data).execute()
        return ControlMapping(**result.data[0])

    # ================================================================
    # INDUSTRY OVERLAYS
    # ================================================================

    def get_overlays_for_control(
        self, control_id: str, industry: Optional[str] = None
    ) -> list[IndustryOverlay]:
        """Get industry-specific overlays for a control."""
        query = (
            self.client.table("industry_overlays")
            .select("*")
            .eq("control_id", control_id)
        )
        if industry:
            query = query.eq("industry", industry)
        result = query.execute()
        return [IndustryOverlay(**row) for row in result.data]

    def create_overlay(self, overlay: IndustryOverlay) -> IndustryOverlay:
        """Insert a new industry overlay."""
        data = overlay.model_dump(exclude_none=True, exclude={"id"})
        if "overlay_type" in data:
            data["overlay_type"] = data["overlay_type"].value if hasattr(data["overlay_type"], "value") else data["overlay_type"]
        result = self.admin.table("industry_overlays").insert(data).execute()
        return IndustryOverlay(**result.data[0])

    # ================================================================
    # EVIDENCE REQUIREMENTS
    # ================================================================

    def get_evidence_for_control(
        self, control_id: str, industry_overlay_id: Optional[str] = None
    ) -> list[EvidenceRequirement]:
        """Get evidence requirements for a control (universal and industry-specific)."""
        # Always get universal requirements (where overlay is null)
        universal = (
            self.client.table("evidence_requirements")
            .select("*")
            .eq("control_id", control_id)
            .is_("industry_overlay_id", "null")
            .execute()
        )
        results = universal.data

        # If industry overlay specified, also get those
        if industry_overlay_id:
            specific = (
                self.client.table("evidence_requirements")
                .select("*")
                .eq("control_id", control_id)
                .eq("industry_overlay_id", industry_overlay_id)
                .execute()
            )
            results += specific.data

        return [EvidenceRequirement(**row) for row in results]

    def create_evidence_requirement(self, req: EvidenceRequirement) -> EvidenceRequirement:
        """Insert a new evidence requirement."""
        data = req.model_dump(exclude_none=True, exclude={"id"})
        if "evidence_type" in data:
            data["evidence_type"] = data["evidence_type"].value if hasattr(data["evidence_type"], "value") else data["evidence_type"]
        result = self.admin.table("evidence_requirements").insert(data).execute()
        return EvidenceRequirement(**result.data[0])

    # ================================================================
    # INTERPRETATIONS (THE MOAT)
    # ================================================================

    def get_interpretations_for_control(
        self, control_id: str, industry_overlay_id: Optional[str] = None
    ) -> list[Interpretation]:
        """Get expert interpretations for a control (universal and industry-specific)."""
        # Universal interpretations
        universal = (
            self.client.table("interpretations")
            .select("*")
            .eq("control_id", control_id)
            .is_("industry_overlay_id", "null")
            .execute()
        )
        results = universal.data

        if industry_overlay_id:
            specific = (
                self.client.table("interpretations")
                .select("*")
                .eq("control_id", control_id)
                .eq("industry_overlay_id", industry_overlay_id)
                .execute()
            )
            results += specific.data

        return [Interpretation(**row) for row in results]

    def create_interpretation(self, interp: Interpretation) -> Interpretation:
        """Insert a new interpretation."""
        data = interp.model_dump(exclude_none=True, exclude={"id"})
        if "interpretation_type" in data:
            data["interpretation_type"] = data["interpretation_type"].value if hasattr(data["interpretation_type"], "value") else data["interpretation_type"]
        result = self.admin.table("interpretations").insert(data).execute()
        return Interpretation(**result.data[0])

    def increment_interpretation_usage(self, interpretation_id: str) -> None:
        """Increment usage count for an interpretation."""
        # Get current count
        result = (
            self.client.table("interpretations")
            .select("usage_count")
            .eq("id", interpretation_id)
            .execute()
        )
        if result.data:
            new_count = (result.data[0].get("usage_count", 0) or 0) + 1
            self.admin.table("interpretations").update(
                {"usage_count": new_count}
            ).eq("id", interpretation_id).execute()

    # ================================================================
    # FEEDBACK (LEARNING LOOP)
    # ================================================================

    def create_feedback(self, feedback: Feedback) -> Feedback:
        """Record a piece of user feedback."""
        data = feedback.model_dump(exclude_none=True, exclude={"id"})
        if "feedback_type" in data:
            data["feedback_type"] = data["feedback_type"].value if hasattr(data["feedback_type"], "value") else data["feedback_type"]
        result = self.admin.table("feedback").insert(data).execute()
        return Feedback(**result.data[0])

    def get_pending_feedback(self) -> list[Feedback]:
        """Get all unreviewed feedback."""
        result = (
            self.client.table("feedback")
            .select("*")
            .eq("applied", False)
            .order("created_at")
            .execute()
        )
        return [Feedback(**row) for row in result.data]

    # ================================================================
    # AUDIT PROCESSES (Process-Centric Layer)
    # ================================================================

    def get_all_audit_processes(self) -> list[AuditProcess]:
        """Get all 30 audit processes."""
        result = (
            self.client.table("audit_processes")
            .select("*")
            .order("code")
            .execute()
        )
        return [AuditProcess(**row) for row in result.data]

    def get_audit_process_by_code(self, code: str) -> Optional[AuditProcess]:
        """Look up a process by code (e.g., 'P04')."""
        result = (
            self.client.table("audit_processes")
            .select("*")
            .eq("code", code)
            .execute()
        )
        if result.data:
            return AuditProcess(**result.data[0])
        return None

    def get_audit_processes_by_category(self, category: str) -> list[AuditProcess]:
        """Get processes by category (e.g., 'Security', 'Operations')."""
        result = (
            self.client.table("audit_processes")
            .select("*")
            .eq("category", category)
            .order("code")
            .execute()
        )
        return [AuditProcess(**row) for row in result.data]

    # ================================================================
    # PROCESS PHASES
    # ================================================================

    def get_phases_for_process(self, audit_process_id: str) -> list[ProcessPhase]:
        """Get all lifecycle phases for a process, ordered by phase_number."""
        result = (
            self.client.table("process_phases")
            .select("*")
            .eq("audit_process_id", audit_process_id)
            .order("phase_number")
            .execute()
        )
        return [ProcessPhase(**row) for row in result.data]

    # ================================================================
    # RISKS
    # ================================================================

    def get_risks_for_process(
        self, audit_process_id: str, phase_id: Optional[str] = None
    ) -> list[Risk]:
        """Get all risks for a process, optionally filtered by phase."""
        query = (
            self.client.table("risks")
            .select("*")
            .eq("audit_process_id", audit_process_id)
        )
        if phase_id:
            query = query.eq("process_phase_id", phase_id)
        result = query.order("risk_code").execute()
        return [Risk(**row) for row in result.data]

    def get_parent_risks_for_process(self, audit_process_id: str) -> list[Risk]:
        """Get only level-1 parent risks for a process."""
        result = (
            self.client.table("risks")
            .select("*")
            .eq("audit_process_id", audit_process_id)
            .eq("risk_level", 1)
            .order("risk_code")
            .execute()
        )
        return [Risk(**row) for row in result.data]

    def get_sub_risks(self, parent_risk_id: str) -> list[Risk]:
        """Get sub-risks for a parent risk."""
        result = (
            self.client.table("risks")
            .select("*")
            .eq("parent_risk_id", parent_risk_id)
            .order("risk_code")
            .execute()
        )
        return [Risk(**row) for row in result.data]

    # ================================================================
    # RISK-CONTROL MAPPINGS
    # ================================================================

    def get_control_mapping_for_risk(self, risk_id: str) -> Optional[RiskControlMapping]:
        """Get the control mapping for a specific sub-risk."""
        result = (
            self.client.table("risk_control_mappings")
            .select("*")
            .eq("risk_id", risk_id)
            .execute()
        )
        if result.data:
            return RiskControlMapping(**result.data[0])
        return None

    def get_all_mappings_for_process(self, audit_process_id: str) -> list[RiskControlMapping]:
        """Get all risk-control mappings for a process.

        Does a two-step query: first gets all risk IDs for the process,
        then fetches all mappings for those risk IDs. Avoids PostgREST
        join filter syntax which the Supabase Python client doesn't support cleanly.
        """
        # Step 1: get every risk ID that belongs to this process
        risk_result = (
            self.client.table("risks")
            .select("id")
            .eq("audit_process_id", audit_process_id)
            .execute()
        )
        risk_ids = [row["id"] for row in risk_result.data]
        if not risk_ids:
            return []

        # Step 2: get all mappings where risk_id is in that set
        mapping_result = (
            self.client.table("risk_control_mappings")
            .select("*")
            .in_("risk_id", risk_ids)
            .execute()
        )
        return [RiskControlMapping(**row) for row in mapping_result.data]

    # ================================================================
    # TESTING PROCEDURES
    # ================================================================

    def get_testing_procedures(self, risk_control_mapping_id: str) -> list[TestingProcedure]:
        """Get ordered test steps for a risk-control mapping."""
        result = (
            self.client.table("testing_procedures")
            .select("*")
            .eq("risk_control_mapping_id", risk_control_mapping_id)
            .order("step_number")
            .execute()
        )
        return [TestingProcedure(**row) for row in result.data]

    # ================================================================
    # EVIDENCE (process-centric, via risk_control_mapping_id)
    # ================================================================

    def get_evidence_for_mapping(self, risk_control_mapping_id: str) -> list[EvidenceRequirement]:
        """Get evidence requirements linked to a risk-control mapping."""
        result = (
            self.client.table("evidence_requirements")
            .select("*")
            .eq("risk_control_mapping_id", risk_control_mapping_id)
            .execute()
        )
        return [EvidenceRequirement(**row) for row in result.data]

    # ================================================================
    # USAGE LOG (TELEMETRY)
    # ================================================================

    def log_usage(self, log: UsageLog) -> None:
        """Record a usage event (errors are ignored)."""
        try:
            data = log.model_dump(exclude_none=True, exclude={"id"})
            self.admin.table("usage_log").insert(data).execute()
        except Exception:
            # Telemetry should never break the main flow
            pass
