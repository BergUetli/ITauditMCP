"""
LLM Engine - Orchestrates analyst + reviewer two-LLM pipeline.
Analyst does primary analysis, reviewer challenges and improves the work.
"""

from dataclasses import dataclass
from typing import Optional
from llm.base import LLMProvider, LLMResponse
from llm.anthropic_provider import AnthropicProvider
from llm.openai_provider import OpenAIProvider
from config.settings import settings


@dataclass
class EngineResult:
    """Result from analyst + reviewer pipeline with individual and final responses."""
    final_output: str
    analyst_response: Optional[LLMResponse] = None
    reviewer_response: Optional[LLMResponse] = None
    reviewer_made_changes: bool = False
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class LLMEngine:
    """Runs a two-LLM pipeline: analyst generates response, reviewer improves it."""

    def __init__(
        self,
        analyst: Optional[LLMProvider] = None,
        reviewer: Optional[LLMProvider] = None,
    ):
        """Initializes analyst and reviewer LLM providers."""
        # Default: Claude as analyst
        if analyst is None:
            if settings.anthropic_api_key:
                self.analyst = AnthropicProvider()
            elif settings.openai_api_key:
                self.analyst = OpenAIProvider()
            else:
                raise ValueError(
                    "No LLM API key configured. "
                    "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env"
                )
        else:
            self.analyst = analyst

        # Default: OpenAI as reviewer (different model provides different perspective)
        if reviewer is None:
            if settings.openai_api_key:
                self.reviewer = OpenAIProvider()
            elif settings.anthropic_api_key:
                # Fall back to Claude if OpenAI not available
                self.reviewer = AnthropicProvider()
            else:
                self.reviewer = None  # No reviewer — single LLM mode
        else:
            self.reviewer = reviewer

    async def analyze(
        self,
        context: str,
        question: str,
        analyst_system_prompt: str,
        reviewer_system_prompt: Optional[str] = None,
        skip_review: bool = False,
    ) -> EngineResult:
        """Runs analyst then reviewer pipeline and returns final output."""
        # ========================================
        # STEP 1: ANALYST
        # ========================================
        # Build the analyst's full prompt with context
        analyst_message = f"""
Here is the relevant audit knowledge context:

{context}

---

Based on the above context, please address the following:

{question}
"""
        analyst_response = await self.analyst.complete(
            system_prompt=analyst_system_prompt,
            user_message=analyst_message,
        )

        # If no reviewer or skip_review, return analyst output directly
        if skip_review or not self.reviewer:
            return EngineResult(
                final_output=analyst_response.content,
                analyst_response=analyst_response,
                total_input_tokens=analyst_response.input_tokens,
                total_output_tokens=analyst_response.output_tokens,
            )

        # ========================================
        # STEP 2: REVIEWER
        # ========================================
        # The reviewer gets the original context AND the analyst's output
        if not reviewer_system_prompt:
            reviewer_system_prompt = DEFAULT_REVIEWER_PROMPT

        reviewer_message = f"""
## Original Context
{context}

## Original Question
{question}

## Analyst's Response
{analyst_response.content}

---

Please review the analyst's response above. Check for:
1. Missing risks or controls that should have been identified
2. Incorrect control ID references
3. Overstated or understated risk ratings
4. Missing or weak evidence requirements
5. Recommendations that aren't actionable

Provide your revised and improved version. If the analyst's work is solid,
confirm it and note any minor improvements.
"""
        reviewer_response = await self.reviewer.complete(
            system_prompt=reviewer_system_prompt,
            user_message=reviewer_message,
        )

        # Check if reviewer output is substantially different from analyst output
        reviewer_made_changes = not self._outputs_similar(
            analyst_response.content, reviewer_response.content
        )

        return EngineResult(
            final_output=reviewer_response.content,
            analyst_response=analyst_response,
            reviewer_response=reviewer_response,
            reviewer_made_changes=reviewer_made_changes,
            total_input_tokens=(
                analyst_response.input_tokens + reviewer_response.input_tokens
            ),
            total_output_tokens=(
                analyst_response.output_tokens + reviewer_response.output_tokens
            ),
        )

    async def analyze_single(
        self,
        context: str,
        question: str,
        system_prompt: str,
    ) -> LLMResponse:
        """Single LLM call without reviewer step for simpler queries."""
        message = f"""
Here is the relevant audit knowledge context:

{context}

---

{question}
"""
        return await self.analyst.complete(
            system_prompt=system_prompt,
            user_message=message,
        )

    def _outputs_similar(self, text1: str, text2: str) -> bool:
        """Checks if two outputs are similar by comparing word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return False
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap > 0.7  # >70% word overlap means outputs are similar


# ================================================================
# Default system prompts
# ================================================================

DEFAULT_REVIEWER_PROMPT = """You are a Senior Audit Reviewer challenging the analyst's work.

Review standards:
- Every control ID must be real (flag anything that looks made up)
- Every finding must have: Condition, Criteria, Cause, Effect, Recommendation
- Risk ratings must match the severity of the issue
- Recommendations must be actionable (not vague)
- Cross-framework mappings must be accurate
- Industry-specific requirements must be addressed

If the work is solid, confirm it and suggest minor improvements.
If there are significant issues, provide a corrected version.

Explain WHY you made changes."""
