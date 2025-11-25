"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://localhost:5432/knowledge_base"

    # Azure OpenAI
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment_gpt4o: str = "gpt-4o"
    azure_openai_deployment_embedding: str = "text-embedding-3-large"

    # OpenAI
    openai_api_key: Optional[str] = None

    # Anthropic
    anthropic_api_key: Optional[str] = None

    # Default Provider
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"

    # MCP (Model Context Protocol)
    mcp_base_url: str = "http://localhost:9000"
    mcp_jira_url: str = "http://localhost:8080"
    mcp_confluence_url: str = "http://localhost:8090"

    # Jira (Local Server)
    jira_url: Optional[str] = None
    jira_username: Optional[str] = None
    jira_email: Optional[str] = None  # For Cloud
    jira_password: Optional[str] = None  # For Local Server
    jira_api_token: Optional[str] = None  # For Cloud
    jira_project_key: Optional[str] = None

    # Confluence (Local Server)
    confluence_url: Optional[str] = None
    confluence_username: Optional[str] = None
    confluence_email: Optional[str] = None  # For Cloud
    confluence_password: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_space_key: Optional[str] = None

    # Google Cloud Storage
    gcs_bucket_name: Optional[str] = None
    google_application_credentials: Optional[str] = None

    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
