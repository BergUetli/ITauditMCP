"""
OpenAI Provider - Supports standard OpenAI and Azure OpenAI APIs.
Used as the reviewer LLM in the analyst+reviewer pattern.
"""

from openai import AsyncOpenAI, AsyncAzureOpenAI
from llm.base import LLMProvider, LLMResponse
from config.settings import settings


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI (standard or Azure) APIs."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.openai_model
        self.is_azure = settings.openai_api_type.lower() == "azure"

        if self.is_azure:
            # Azure uses endpoint and API version configuration
            self.client = AsyncAzureOpenAI(
                api_key=api_key or settings.openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
            # Azure requires deployment name instead of model name
            self.model = settings.azure_openai_deployment or self.model
        else:
            # Standard OpenAI client
            self.client = AsyncOpenAI(
                api_key=api_key or settings.openai_api_key
            )

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Calls OpenAI/Azure OpenAI API and returns structured response."""
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            provider="azure_openai" if self.is_azure else "openai",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
