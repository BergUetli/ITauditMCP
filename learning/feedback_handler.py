"""
Manages user feedback and knowledge base updates.
Nothing changes without RP's approval.
"""

from typing import Optional
from knowledge.store import KnowledgeStore
from knowledge.models import (
    Feedback, FeedbackType, ControlMapping, Interpretation
)


class FeedbackHandler:
    """Manages user corrections and approvals for the knowledge base."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self.store = store or KnowledgeStore()

    def submit_correction(
        self,
        entity_type: str,
        entity_id: str,
        original: str,
        corrected: str,
        user_id: str = "anonymous",
        source: str = "mcp_server",
    ) -> Feedback:
        """Submit a correction to the review queue."""
        feedback = Feedback(
            source_product=source,
            user_id=user_id,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            feedback_type=FeedbackType.CORRECTION,
            original_output=original,
            corrected_output=corrected,
        )
        return self.store.create_feedback(feedback)

    def submit_confirmation(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str = "anonymous",
        source: str = "mcp_server",
    ) -> Feedback:
        """Record that a user confirmed an output was correct."""
        feedback = Feedback(
            source_product=source,
            user_id=user_id,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            feedback_type=FeedbackType.CONFIRMATION,
            applied=True,  # Auto-applied
            applied_to=entity_type,
        )
        created = self.store.create_feedback(feedback)

        # Auto-boost confidence on the entity
        self._boost_confidence(entity_type, entity_id, boost=0.02)

        return created

    def get_pending_review(self) -> list[Feedback]:
        """Retrieve all feedback pending RP's approval."""
        return self.store.get_pending_feedback()

    def approve_feedback(self, feedback_id: str) -> bool:
        """Approve feedback and apply the correction to the knowledge base."""
        result = (
            self.store.client.table("feedback")
            .select("*")
            .eq("id", feedback_id)
            .execute()
        )
        if not result.data:
            return False

        fb = Feedback(**result.data[0])

        if fb.feedback_type == FeedbackType.CORRECTION:
            self._apply_correction(fb)

        self.store.admin.table("feedback").update({
            "applied": True,
            "applied_to": fb.related_entity_type,
        }).eq("id", feedback_id).execute()

        self._reduce_confidence(
            fb.related_entity_type,
            fb.related_entity_id,
            reduction=0.05
        )

        return True

    def reject_feedback(self, feedback_id: str) -> bool:
        """Reject feedback without applying changes."""
        self.store.admin.table("feedback").update({
            "applied": True,
            "applied_to": "rejected",
        }).eq("id", feedback_id).execute()
        return True

    def _apply_correction(self, feedback: Feedback) -> None:
        """Update the knowledge base based on the feedback type."""
        if feedback.related_entity_type == "mapping":
            self.store.admin.table("control_mappings").update({
                "rationale": feedback.corrected_output,
            }).eq("id", feedback.related_entity_id).execute()

        elif feedback.related_entity_type == "interpretation":
            self.store.admin.table("interpretations").update({
                "content": feedback.corrected_output,
                "is_validated": True,
            }).eq("id", feedback.related_entity_id).execute()

        elif feedback.related_entity_type == "evidence_req":
            self.store.admin.table("evidence_requirements").update({
                "description": feedback.corrected_output,
            }).eq("id", feedback.related_entity_id).execute()

    def _boost_confidence(
        self, entity_type: str, entity_id: str, boost: float = 0.02
    ) -> None:
        """Increase the confidence score for a knowledge base entry."""
        table_map = {
            "mapping": "control_mappings",
            "interpretation": "interpretations",
        }
        table = table_map.get(entity_type)
        if not table:
            return

        field = "confidence_score" if entity_type == "mapping" else "confidence"

        result = (
            self.store.client.table(table)
            .select(field)
            .eq("id", entity_id)
            .execute()
        )
        if result.data:
            current = result.data[0].get(field, 0.5) or 0.5
            new_score = min(1.0, current + boost)
            self.store.admin.table(table).update({
                field: new_score
            }).eq("id", entity_id).execute()

    def _reduce_confidence(
        self, entity_type: str, entity_id: str, reduction: float = 0.05
    ) -> None:
        """Decrease the confidence score for a knowledge base entry."""
        table_map = {
            "mapping": "control_mappings",
            "interpretation": "interpretations",
        }
        table = table_map.get(entity_type)
        if not table:
            return

        field = "confidence_score" if entity_type == "mapping" else "confidence"

        result = (
            self.store.client.table(table)
            .select(field)
            .eq("id", entity_id)
            .execute()
        )
        if result.data:
            current = result.data[0].get(field, 0.5) or 0.5
            new_score = max(0.0, current - reduction)
            self.store.admin.table(table).update({
                field: new_score
            }).eq("id", entity_id).execute()
