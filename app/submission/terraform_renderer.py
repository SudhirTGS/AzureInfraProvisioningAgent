"""Deterministic (no LLM) Jinja2 rendering of Terraform files.

Generic by resource_type, same drop-in-a-folder pattern as the schema
loader: a new resource type just needs a `terraform_templates/<type>/*.j2`
directory and it's picked up automatically.
"""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import Settings, get_settings


@lru_cache
def _env() -> Environment:
    templates_dir = get_settings().terraform_templates_dir
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def compute_slug(resource_type: str, requirements: dict) -> str:
    """A short, filesystem/branch-name-safe identifier for a single
    provisioning request, used for the state key, the PR branch name, and
    the infra/<type>/<slug>/ commit path."""
    if resource_type == "azure_sql_database":
        return f"{requirements['sql_server_name']}-{requirements['database_name']}".lower()
    # Generic fallback for future resource types that haven't defined a more
    # readable slug scheme yet.
    digest = hashlib.sha1(json.dumps(requirements, sort_keys=True).encode()).hexdigest()[:8]
    return f"{resource_type}-{digest}"


def render_resource(
    resource_type: str, normalized_requirements: dict, settings: Settings | None = None
) -> dict[str, str]:
    """Render every Jinja2 template for a resource type into {filename: content}."""
    settings = settings or get_settings()
    env = _env()
    templates_dir = settings.terraform_templates_dir

    slug = compute_slug(resource_type, normalized_requirements)
    # The state backend's resource group defaults to the request's own
    # resource_group when no app-wide TERRAFORM_STATE_RESOURCE_GROUP is
    # configured, so a single-RG setup doesn't need separate backend config.
    # The storage account/container still have no per-request equivalent in
    # the schema and must come from settings.
    tf_state_resource_group = settings.terraform_state_resource_group or normalized_requirements.get(
        "resource_group", ""
    )
    context = {
        **normalized_requirements,
        "azurerm_provider_version": settings.terraform_azurerm_provider_version,
        "tf_state_resource_group": tf_state_resource_group,
        "tf_state_storage_account": settings.terraform_state_storage_account,
        "tf_state_container": settings.terraform_state_container,
        "tf_state_key": f"{resource_type}/{slug}.tfstate",
    }

    template_paths: list[Path] = []
    resource_dir = templates_dir / resource_type
    if resource_dir.exists():
        template_paths.extend(sorted(resource_dir.glob("*.j2")))
    common_dir = templates_dir / "common"
    if common_dir.exists():
        template_paths.extend(sorted(common_dir.glob("*.j2")))

    rendered: dict[str, str] = {}
    for path in template_paths:
        relative = path.relative_to(templates_dir).as_posix()
        template = env.get_template(relative)
        output_name = path.name.removesuffix(".j2")
        rendered[output_name] = template.render(**context)

    return rendered
