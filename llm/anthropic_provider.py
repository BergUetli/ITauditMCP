"""
Anthropic Provider - Connects to Claude models via the Anthropic API.
Used as the primary analyst LLM for risk identification and control mapping.
"""

import anthropic
from llm.base import LLMProvider, LLMResponse
from config.settings import settings


class AnthropicProvider(LLMProvider):
    """LLM provider for Anthropic Claude models."""

    def __init__(self, model: str = None, api_key: str = None):
        """Initializes with model and API key from settings or overrides."""
        self.model = model or settings.anthropic_model
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.anthropic_api_key
        )

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Calls Claude API and returns structured response."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Extract text blocks from Claude's response
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            model=self.model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
