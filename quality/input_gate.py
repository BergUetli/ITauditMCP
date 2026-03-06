"""
Input Gate - Validates and normalizes audit input before LLM processing.
Catches bad data early, normalizes framework names, and classifies input type.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class InputType(str, Enum):
    """Categories of audit input the system recognizes."""
    PROCESS_DESCRIPTION = "process_description"
    CONTROL_REFERENCE = "control_reference"
    EVIDENCE_ARTIFACT = "evidence_artifact"
    RISK_DESCRIPTION = "risk_description"
    FRAMEWORK_QUERY = "framework_query"
    FINDING_DRAFT = "finding_draft"
    UNKNOWN = "unknown"


@dataclass
class InputValidation:
    """Result of input validation with detected frameworks, controls, and classification."""
    is_valid: bool = True
    input_type: InputType = InputType.UNKNOWN
    detected_frameworks: list[str] = field(default_factory=list)
    detected_control_ids: list[str] = field(default_factory=list)
    detected_industry: Optional[str] = None
    normalized_text: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class InputGate:
    """Validates and classifies input text before LLM processing."""

    # ================================================================
    # FRAMEWORK DETECTION PATTERNS
    # ================================================================
    # Maps common framework names to standardized identifiers
    FRAMEWORK_PATTERNS: dict[str, list[str]] = {
        "cobit_2019": [
            r"\bcobit\b",
            r"\bcobit\s*2019\b",
            r"\bcobit\s*5\b",
            r"\bisaca\s+framework\b",
        ],
        "iso_27001_2022": [
            r"\biso\s*27001\b",
            r"\b27001\b",
            r"\biso\s*27001:2022\b",
            r"\bisms\b",  # Information Security Management System
        ],
        "nist_csf_2": [
            r"\bnist\s*csf\b",
            r"\bnist\s+cybersecurity\s+framework\b",
            r"\bcsf\s*2\.0\b",
            r"\bnist\s+csf\s*2\b",
        ],
        "ffiec_it": [
            r"\bffiec\b",
            r"\bit\s+handbook\b",
            r"\bffiec\s+it\b",
            r"\bfederal\s+financial\b",
        ],
        "soc2_tsc": [
            r"\bsoc\s*2\b",
            r"\bsoc\s*ii\b",
            r"\btrust\s+services?\s+criteria\b",
            r"\btsc\b",
            r"\baicpa\b",
        ],
    }

    # ================================================================
    # CONTROL ID PATTERNS
    # ================================================================
    # Regex patterns matching control ID formats for each framework
    CONTROL_ID_PATTERNS: dict[str, str] = {
        # COBIT: EDM01.01, APO01.02, BAI06.01, DSS01.03, MEA01.01
        "cobit_2019": r"\b(EDM|APO|BAI|DSS|MEA)\d{2}\.\d{2}\b",

        # ISO 27001: A.5.1, A.6.1.2, A.8.32
        "iso_27001_2022": r"\bA\.\d{1,2}(?:\.\d{1,2}){0,2}\b",

        # NIST CSF: ID.AM-1, PR.DS-1, DE.CM-8, GV.OC-01
        "nist_csf_2": r"\b(GV|ID|PR|DE|RS|RC)\.[A-Z]{2}-\d{1,2}\b",

        # SOC 2: CC1.1, CC6.1, A1.1, PI1.1
        "soc2_tsc": r"\b(CC|A|PI|P|C)\d\.\d\b",
    }

    # ================================================================
    # INDUSTRY DETECTION
    # ================================================================
    INDUSTRY_PATTERNS: dict[str, list[str]] = {
        "banking": [
            r"\bbank(?:ing)?\b", r"\bfinancial\s+institution\b",
            r"\bocc\b", r"\bfederal\s+reserve\b", r"\bfdic\b",
            r"\bfed\s+exam\b", r"\bexaminer\b", r"\bcra\b",
            r"\bbsa\b", r"\baml\b", r"\bkyc\b",
        ],
        "healthcare": [
            r"\bhipaa\b", r"\bhealthcare\b", r"\bhealth\s+system\b",
            r"\bphi\b", r"\bephi\b", r"\bhhs\b",
            r"\bhitech\b", r"\bcovered\s+entity\b",
        ],
        "retail": [
            r"\bpci\s*dss\b", r"\bpayment\s+card\b", r"\bretail\b",
            r"\bmerchant\b", r"\bcardholder\b", r"\bpos\b",
        ],
        "government": [
            r"\bfederal\b", r"\bfisma\b", r"\bfedramp\b",
            r"\bnist\s+800\b", r"\bgovernment\b",
        ],
    }

    # ================================================================
    # INPUT TYPE CLASSIFICATION
    # ================================================================
    INPUT_TYPE_PATTERNS: dict[InputType, list[str]] = {
        InputType.PROCESS_DESCRIPTION: [
            r"\bprocess\b.*\b(is|works|flow|step)",
            r"\bworkflow\b", r"\bprocedure\b",
            r"\bfirst\s*,?\s*(we|they|the)\b",
            r"\bthen\s*,?\s*(we|they|the)\b",
            r"\bwho\s+does\b", r"\bresponsible\s+for\b",
        ],
        InputType.RISK_DESCRIPTION: [
            r"\brisk\b", r"\bthreat\b", r"\bvulnerability\b",
            r"\bcould\s+(result|lead|cause)\b",
            r"\bunauthorized\b", r"\bfraud\b",
            r"\bdata\s+(breach|loss|leak)\b",
        ],
        InputType.CONTROL_REFERENCE: [
            r"\bcontrol\b", r"\btest\b.*\bcontrol\b",
            r"\bevaluate\b.*\bcontrol\b",
            r"\bassess\b",
        ],
        InputType.EVIDENCE_ARTIFACT: [
            r"\bevidence\b", r"\breport\b.*\bshows\b",
            r"\blog\b.*\b(shows|indicates)\b",
            r"\bscreenshot\b", r"\bconfiguration\b",
            r"\battach(ed|ment)\b",
        ],
        InputType.FINDING_DRAFT: [
            r"\bfinding\b", r"\bcondition\b.*\bcriteria\b",
            r"\bwe\s+found\s+that\b", r"\bdeficiency\b",
            r"\bgap\b.*\bcontrol\b",
        ],
    }

    def validate(self, text: str) -> InputValidation:
        """Validates input and returns detected frameworks, controls, and input type."""
        result = InputValidation()
        result.normalized_text = text.strip()

        # Check for empty input
        if not text or not text.strip():
            result.is_valid = False
            result.errors.append("Input is empty")
            return result

        # Run all detection passes
        text_lower = text.lower()

        # 1. Detect frameworks mentioned
        result.detected_frameworks = self._detect_frameworks(text_lower)

        # 2. Detect specific control IDs
        result.detected_control_ids = self._detect_control_ids(text)

        # 3. Detect industry
        result.detected_industry = self._detect_industry(text_lower)

        # 4. Classify input type
        result.input_type = self._classify_input(text_lower)

        # 5. If control IDs were found, verify they match a known framework
        if result.detected_control_ids and not result.detected_frameworks:
            # Try to infer framework from control ID format
            for ctrl_id in result.detected_control_ids:
                inferred = self._infer_framework_from_control_id(ctrl_id)
                if inferred and inferred not in result.detected_frameworks:
                    result.detected_frameworks.append(inferred)
                    result.warnings.append(
                        f"Framework inferred from control ID '{ctrl_id}': {inferred}"
                    )

        return result

    def _detect_frameworks(self, text_lower: str) -> list[str]:
        """Finds all framework names mentioned in the text."""
        found = []
        for slug, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if slug not in found:
                        found.append(slug)
                    break  # One match per framework is enough
        return found

    def _detect_control_ids(self, text: str) -> list[str]:
        """Finds specific control ID codes in the text."""
        found = []
        for framework, pattern in self.CONTROL_ID_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            # findall returns groups if the pattern has groups, so handle both
            for match in matches:
                if isinstance(match, tuple):
                    # If regex had groups, re-search to get the full matched ID
                    for full_match in re.finditer(pattern, text, re.IGNORECASE):
                        match_str = full_match.group(0)
                        if match_str not in found:
                            found.append(match_str)
                else:
                    if match not in found:
                        found.append(match)
        return found

    def _detect_industry(self, text_lower: str) -> Optional[str]:
        """Finds the first industry reference in the text."""
        for industry, patterns in self.INDUSTRY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return industry
        return None

    def _classify_input(self, text_lower: str) -> InputType:
        """Classifies input type based on keywords and patterns."""
        # Check for control IDs first since it's most specific
        for pattern in self.CONTROL_ID_PATTERNS.values():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return InputType.CONTROL_REFERENCE

        # Check other patterns
        for input_type, patterns in self.INPUT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return input_type

        return InputType.UNKNOWN

    def _infer_framework_from_control_id(self, control_id: str) -> Optional[str]:
        """Determines which framework a control ID belongs to by its format."""
        for framework_slug, pattern in self.CONTROL_ID_PATTERNS.items():
            if re.match(pattern, control_id, re.IGNORECASE):
                return framework_slug
        return None
