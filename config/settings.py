# Loads all settings from the .env file.
# Other files import 'settings' from here to get API keys, DB URLs, etc.

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All config values. Reads from .env file automatically."""

    # --- Supabase ---
    supabase_url: str = Field(
        description="Your Supabase project URL (e.g., https://xxx.supabase.co)"
    )
    supabase_anon_key: str = Field(
        description="Supabase anon/public key - used for read operations"
    )
    supabase_service_key: str = Field(
        default="",
        description="Supabase service role key - used for write operations. "
        "Only needed for admin tasks like seeding data."
    )

    # --- Anthropic (Claude) ---
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude models"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Which Claude model to use for analysis"
    )

    # --- OpenAI / Azure OpenAI ---
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (standard or Azure)"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="Which OpenAI model to use"
    )
    openai_api_type: str = Field(
        default="openai",
        description="'openai' for standard, 'azure' for Azure OpenAI"
    )
    azure_openai_endpoint: str = Field(
        default="",
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-01",
        description="Azure OpenAI API version"
    )
    azure_openai_deployment: str = Field(
        default="",
        description="Azure OpenAI deployment name"
    )

    # --- MCP Server ---
    mcp_transport: str = Field(
        default="stdio",
        description="'stdio' for local/Claude Desktop, 'streamable-http' for remote"
    )
    mcp_host: str = Field(default="0.0.0.0")
    mcp_port: int = Field(default=8000)

    # --- Quality Layer ---
    min_confidence_threshold: float = Field(
        default=0.5,
        description="Minimum confidence score (0-1) to include results"
    )

    # --- Learning Loop ---
    require_human_review: bool = Field(
        default=True,
        description="If True, corrections need RP's approval before applying"
    )

    class Config:
        # Tell Pydantic to read from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


# One shared instance — the whole app uses this
settings = Settings()
