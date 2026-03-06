"""Data models for all audit entities (frameworks, controls, mappings, evidence).
Matches Supabase schema exactly and auto-generates MCP tool schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


# Enum values for control and audit attributes.
# Pydantic rejects invalid values (e.g., control_type="banana").

class ControlType(str, Enum):
    """How a control works - does it prevent, detect, or fix problems?"""
    PREVENTIVE = "preventive"   # Stops bad things before they happen (e.g., access controls)
    DETECTIVE = "detective"     # Finds bad things after they happen (e.g., log monitoring)
    CORRECTIVE = "corrective"   # Fixes bad things once found (e.g., incident response)


class AutomationLevel(str, Enum):
    """How much of this control is automated vs manual?"""
    MANUAL = "manual"           # Human does it entirely (e.g., reviewing reports)
    SEMI_AUTO = "semi_auto"     # Mix of human and system (e.g., system flags, human reviews)
    FULLY_AUTO = "fully_auto"   # System handles it entirely (e.g., automated backup)


class MappingStrength(str, Enum):
    """How closely two controls from different frameworks relate."""
    EXACT = "exact"         # Controls are essentially the same requirement
    STRONG = "strong"       # Controls cover the same area with minor differences
    PARTIAL = "partial"     # Some overlap, but significant gaps between them
    RELATED = "related"     # Same general topic, but different requirements


class MappingDirection(str, Enum):
    """Which way does a control mapping work?"""
    BIDIRECTIONAL = "bidirectional"       # A satisfies B, and B satisfies A
    SOURCE_TO_TARGET = "source_to_target" # A satisfies B, but not vice versa


class EvidenceType(str, Enum):
    """What kind of proof satisfies this control?"""
    DOCUMENT = "document"       # Written policy, procedure, report
    LOG = "log"                 # System log, audit trail
    CONFIG = "config"           # System configuration, settings screenshot
    INTERVIEW = "interview"     # Conversation with control owner
    OBSERVATION = "observation" # Auditor directly witnesses the control working
    SCREENSHOT = "screenshot"   # Screen capture of a system state
    REPORT = "report"           # Generated report from a tool or system


class OverlayType(str, Enum):
    """How does an industry regulation modify a base framework control?"""
    ADDITIONAL_REQ = "additional_req"         # Adds requirements on top
    STRICTER_THRESHOLD = "stricter_threshold" # Same requirement, higher bar
    DIFFERENT_EVIDENCE = "different_evidence" # Needs different proof
    DIFFERENT_SCOPE = "different_scope"       # Applies to different things


class InterpretationType(str, Enum):
    """Categories of expert insight from audit experience."""
    PRACTICAL_GUIDANCE = "practical_guidance"     # "Here's how to actually do this"
    COMMON_PITFALL = "common_pitfall"             # "Auditors often get tripped up by..."
    EXAMINER_EXPECTATION = "examiner_expectation" # "What the examiner REALLY wants"
    TESTING_TIP = "testing_tip"                   # "Best way to test this control"
    EVIDENCE_SHORTCUT = "evidence_shortcut"       # "Fastest way to get good evidence"
    RED_FLAG = "red_flag"                         # "If you see this, dig deeper"


class FeedbackType(str, Enum):
    """What kind of feedback did the user provide?"""
    CORRECTION = "correction"     # "That answer was wrong, here's the right one"
    ADDITION = "addition"         # "Good answer, but also consider..."
    CONFIRMATION = "confirmation" # "That's exactly right" (boosts confidence)
    REJECTION = "rejection"       # "That whole answer is off base"
    ENHANCEMENT = "enhancement"   # "Could be better if..."


# ================================================================
# Core Models - these match the Supabase tables
# ================================================================

class Framework(BaseModel):
    """An audit standard or regulation (e.g., COBIT 2019, ISO 27001:2022)."""
    id: Optional[str] = None
    slug: str = Field(description="URL-friendly identifier (e.g., 'cobit_2019')")
    name: str = Field(description="Display name (e.g., 'COBIT 2019')")
    version: str = Field(description="Version (e.g., '2019', '2022')")
    issuing_body: str = Field(description="Publisher (e.g., 'ISACA', 'NIST')")
    scope: str = Field(description="Area covered (e.g., 'it_governance', 'infosec')")
    is_certifiable: bool = Field(
        default=False,
        description="True if organizations can be certified"
    )
    last_updated: Optional[date] = None
    source_updated: Optional[date] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class Domain(BaseModel):
    """A logical grouping of controls within a framework."""
    id: Optional[str] = None
    framework_id: str = Field(description="Parent framework ID")
    code: str = Field(description="Short code (e.g., 'EDM', 'A.5', 'ID')")
    name: str = Field(description="Full name")
    description: Optional[str] = ""
    hierarchy_level: int = Field(
        default=1,
        description="1=top, 2=sub, 3=sub-sub"
    )
    parent_domain_id: Optional[str] = Field(
        default=None,
        description="Parent domain ID (if nested)"
    )
    sort_order: Optional[int] = 0
    metadata: Optional[dict] = Field(default_factory=dict)


class Control(BaseModel):
    """A single control objective that auditors test."""
    id: Optional[str] = None
    framework_id: str
    domain_id: str
    control_id_code: str = Field(description="Official identifier (e.g., 'BAI06.01')")
    title: str = Field(description="Control name from framework")
    description: Optional[str] = ""
    objective: Optional[str] = Field(default="", description="Control goal")
    guidance: Optional[str] = Field(default="", description="Implementation guidance")
    testing_procedure: Optional[str] = Field(default="", description="How to test it")
    control_type: Optional[ControlType] = ControlType.PREVENTIVE
    automation_level: Optional[AutomationLevel] = AutomationLevel.MANUAL
    regex_pattern: Optional[str] = Field(
        default="",
        description="Regex to match control in free text"
    )
    aliases: Optional[list[str]] = Field(
        default_factory=list,
        description="Alternative names auditors use"
    )
    metadata: Optional[dict] = Field(default_factory=dict)


class ControlMapping(BaseModel):
    """Connects equivalent controls across different frameworks."""
    id: Optional[str] = None
    source_control_id: str
    target_control_id: str
    mapping_strength: MappingStrength
    mapping_direction: MappingDirection = MappingDirection.BIDIRECTIONAL
    rationale: Optional[str] = ""
    validated_by: Optional[str] = ""
    confidence_score: Optional[float] = Field(
        default=0.5,
        description="0.0-1.0 confidence in mapping (starts 0.5)"
    )
    last_validated: Optional[datetime] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class IndustryOverlay(BaseModel):
    """Industry-specific modifications to a control requirement."""
    id: Optional[str] = None
    industry: str = Field(description="Industry (e.g., 'banking', 'healthcare')")
    regulatory_body: str = Field(description="Regulator (e.g., 'OCC', 'FFIEC')")
    regulation_ref: str = Field(description="Specific regulation section")
    control_id: str
    overlay_type: OverlayType
    description: str
    effective_date: Optional[date] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class EvidenceRequirement(BaseModel):
    """What proof is needed to verify a control is working."""
    id: Optional[str] = None
    control_id: Optional[str] = None
    industry_overlay_id: Optional[str] = Field(
        default=None,
        description="Industry-specific requirement (None=universal)"
    )
    evidence_type: EvidenceType
    description: str
    is_mandatory: bool = True
    sampling_guidance: Optional[str] = ""
    retention_period: Optional[str] = ""
    typical_sources: Optional[list[str]] = Field(
        default_factory=list,
        description="Common tools/systems for this evidence"
    )
    metadata: Optional[dict] = Field(default_factory=dict)


class Interpretation(BaseModel):
    """Expert insight on how to approach a control in practice."""
    id: Optional[str] = None
    control_id: str
    industry_overlay_id: Optional[str] = None
    interpretation_type: InterpretationType
    content: str = Field(description="The expert insight")
    source_type: Optional[str] = "expert_experience"
    confidence: Optional[float] = Field(
        default=0.7,
        description="0.0-1.0 confidence (rises on confirm, drops on correction)"
    )
    created_by: Optional[str] = "rp"
    is_validated: bool = False
    usage_count: int = 0
    metadata: Optional[dict] = Field(default_factory=dict)


class Feedback(BaseModel):
    """User corrections and confirmations that improve the system."""
    id: Optional[str] = None
    source_product: str = Field(description="'mcp_server' or 'voice_saas'")
    user_id: Optional[str] = "anonymous"
    related_entity_type: str = Field(
        description="Type: control, mapping, interpretation, evidence_req, overlay"
    )
    related_entity_id: str
    feedback_type: FeedbackType
    original_output: Optional[str] = ""
    corrected_output: Optional[str] = ""
    applied: bool = False
    applied_to: Optional[str] = ""
    metadata: Optional[dict] = Field(default_factory=dict)


# ================================================================
# Process-Centric Models (audit_processes, phases, risks, controls)
# ================================================================

class AuditProcess(BaseModel):
    """An IT audit topic (e.g., Change Management, Access Management)."""
    id: Optional[str] = None
    code: str = Field(description="Process code (e.g., 'P04', 'P07')")
    name: str = Field(description="Display name (e.g., 'Change Management / SDLC')")
    description: Optional[str] = ""
    category: Optional[str] = Field(default="", description="Grouping (e.g., 'Security', 'Operations')")
    banking_priority: Optional[str] = Field(default="MEDIUM", description="CRITICAL/HIGH/MEDIUM/LOW for banking")
    is_gitc: bool = Field(default=True, description="True if this is a General IT Control")
    metadata: Optional[dict] = Field(default_factory=dict)


class ProcessPhase(BaseModel):
    """A lifecycle phase within an audit process (e.g., 'Provisioning' within Access Mgmt)."""
    id: Optional[str] = None
    audit_process_id: str
    phase_number: int = Field(description="Order within the process")
    name: str
    description: Optional[str] = ""


class Risk(BaseModel):
    """A risk or sub-risk within an audit process phase."""
    id: Optional[str] = None
    audit_process_id: str
    process_phase_id: str
    parent_risk_id: Optional[str] = Field(default=None, description="Parent risk ID if this is a sub-risk")
    risk_code: str = Field(description="Hierarchical code (e.g., 'CM1.1.1')")
    description: str
    risk_level: int = Field(default=1, description="1=parent risk, 2=sub-risk")


class RiskControlMapping(BaseModel):
    """Maps a sub-risk to its expected control with framework references."""
    id: Optional[str] = None
    risk_id: str
    control_description: str = Field(description="What the control should do")
    control_type: Optional[ControlType] = ControlType.PREVENTIVE
    framework_refs: Optional[str] = Field(default="", description="Comma-separated framework references")


class TestingProcedure(BaseModel):
    """A step-by-step audit test procedure for a risk-control mapping."""
    id: Optional[str] = None
    risk_control_mapping_id: str
    step_number: int
    procedure: str = Field(description="What the auditor should do")


class UsageLog(BaseModel):
    """Tracks tool calls and control queries for analysis and optimization."""
    id: Optional[str] = None
    tool_name: str
    input_summary: Optional[str] = ""
    controls_retrieved: Optional[list[str]] = Field(default_factory=list)
    frameworks_referenced: Optional[list[str]] = Field(default_factory=list)
    industry: Optional[str] = ""
    llm_provider: Optional[str] = ""
    confidence_score: Optional[float] = 0
    response_time_ms: Optional[int] = 0
    metadata: Optional[dict] = Field(default_factory=dict)
