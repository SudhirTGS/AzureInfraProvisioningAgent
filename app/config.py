"""Central, typed configuration.

Every externalized value (OpenAI, Azure, GitHub, Terraform state backend, ...)
lives here and only here. No other module should read `os.environ` directly —
that keeps a future secret-source swap (e.g. Azure Key Vault) a one-file change
instead of a repo-wide hunt for `os.environ` calls.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- OpenAI ---
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # --- Azure service principal (reserved; Actions use OIDC instead) ---
    azure_tenant_id: str | None = None
    azure_subscription_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None

    # --- GitHub target repo for generated Terraform + PRs ---
    github_token: str | None = None
    github_repo_owner: str = ""
    github_repo_name: str = ""
    github_base_branch: str = "main"
    github_pr_branch_prefix: str = "infra-request/"

    # --- Terraform remote state backend (azurerm) ---
    terraform_state_resource_group: str = ""
    terraform_state_storage_account: str = ""
    terraform_state_container: str = "tfstate"
    terraform_azurerm_provider_version: str = "~> 3.90"

    # --- Submission behavior ---
    submit_requirements_mode: Literal["stub", "render_only", "full_pr"] = "stub"

    # --- Paths ---
    schemas_dir: Path = Path("schemas")
    terraform_templates_dir: Path = Path("terraform_templates")
    rendered_output_dir: Path = Path("rendered_output")

    # --- Session management ---
    session_ttl_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
