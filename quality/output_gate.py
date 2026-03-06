"""
Output Gate - Validates LLM output for hallucinations and finding structure.
Verifies control IDs exist, checks finding completeness, and scores confidence.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from knowledge.store import KnowledgeStore


@dataclass
class OutputValidation:
    """Result of LLM output validation with confidence score and verified controls."""
    is_valid: bool = True
    validated_output: str = ""
    confidence_score: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    verified_control_ids: list[str] = field(default_factory=list)
    unverified_control_ids: list[str] = field(default_factory=list)


# Required components of an audit finding
FINDING_COMPONENTS = [
    "condition",
    "criteria",
    "cause",
    "effect",
    "recommendation",
]


class OutputGate:
    """Validates LLM output for factual errors and completeness."""

    # Regex patterns for control IDs
    CONTROL_ID_PATTERNS = {
        "cobit_2019": r"\b(EDM|APO|BAI|DSS|MEA)\d{2}\.\d{2}\b",
        "iso_27001_2022": r"\bA\.\d{1,2}(?:\.\d{1,2}){0,2}\b",
        "nist_csf_2": r"\b(GV|ID|PR|DE|RS|RC)\.[A-Z]{2}-\d{1,2}\b",
        "soc2_tsc": r"\b(CC|A|PI|P|C)\d\.\d\b",
    }

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self.store = store or KnowledgeStore()

    def validate(self, llm_output: str) -> OutputValidation:
        """Validates LLM output and scores confidence based on verifiable facts."""
        result = OutputValidation()
        result.validated_output = llm_output

        # 1. Extract and verify all control IDs mentioned in the output
        self._verify_control_ids(llm_output, result)

        # 2. Check finding structure (if the output looks like a finding)
        if self._looks_like_finding(llm_output):
            self._check_finding_structure(llm_output, result)

        # 3. Calculate confidence score
        total_ids = len(result.verified_control_ids) + len(result.unverified_control_ids)
        if total_ids > 0:
            result.confidence_score = len(result.verified_control_ids) / total_ids
        else:
            # No control IDs to verify — confidence is based on structure
            result.confidence_score = 0.7  # Neutral default

        # 4. Mark as invalid if there are errors
        if result.errors:
            result.is_valid = False

        return result

    def _verify_control_ids(self, text: str, result: OutputValidation) -> None:
        """Checks if control IDs in the output actually exist in our database."""
        all_ids = set()
        for framework, pattern in self.CONTROL_ID_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                all_ids.add(match.group(0))

        for control_id in all_ids:
            # Try to find this control in any framework
            found = False
            for fw_slug in ["cobit_2019", "iso_27001_2022", "nist_csf_2", "soc2_tsc", "ffiec_it"]:
                control = self.store.get_control_by_code(fw_slug, control_id)
                if control:
                    result.verified_control_ids.append(control_id)
                    found = True
                    break

            if not found:
                result.unverified_control_ids.append(control_id)
                result.warnings.append(
                    f"Control ID '{control_id}' not found in knowledge base. "
                    f"This might be a hallucination or a control we haven't loaded yet."
                )

    def _looks_like_finding(self, text: str) -> bool:
        """Checks if the output looks like an audit finding based on keywords."""
        finding_keywords = [
            r"\bfinding\b", r"\bcondition\b", r"\bcriteria\b",
            r"\bcause\b", r"\beffect\b", r"\brecommendation\b",
            r"\bdeficiency\b", r"\bgap\b", r"\bweakness\b",
        ]
        matches = sum(
            1 for kw in finding_keywords
            if re.search(kw, text, re.IGNORECASE)
        )
        return matches >= 2  # At least 2 finding-related keywords

    def _check_finding_structure(self, text: str, result: OutputValidation) -> None:
        """Checks that finding output includes all 5 required components."""
        text_lower = text.lower()
        missing = []
        for component in FINDING_COMPONENTS:
            # Look for the component name as a header or label
            patterns = [
                rf"\b{component}\b\s*:",
                rf"\*\*{component}\*\*",
                rf"#{1,3}\s*{component}",
            ]
            found = any(
                re.search(p, text_lower, re.IGNORECASE)
                for p in patterns
            )
            if not found:
                missing.append(component)

        if missing:
            result.warnings.append(
                f"Finding may be missing components: {', '.join(missing)}. "
                f"A complete finding needs: {', '.join(FINDING_COMPONENTS)}"
            )
