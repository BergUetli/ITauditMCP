"""
LLM Base Provider - Abstract interface for different LLM implementations.
Each provider (Anthropic, OpenAI, etc.) implements the complete() method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider with usage metrics."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost_usd: Optional[float] = None


class LLMProvider(ABC):
    """Base interface that all LLM providers implement."""

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Sends prompts to the LLM and returns structured response."""
        pass
