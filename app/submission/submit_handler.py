"""The `submit_requirements` tool handler.

Deterministic, non-LLM. Behavior is controlled by SUBMIT_REQUIREMENTS_MODE so
the same code path carries a request from "log only" through "render
Terraform locally" to "open a real GitHub PR" as the mode is flipped —
there's no separate stub implementation to throw away later.
"""

import logging

from app.config import get_settings
from app.submission.terraform_renderer import compute_slug, render_resource
from app.tools.validators import validate_requirements

logger = logging.getLogger(__name__)


def submit_requirements(resource_type: str, requirements: dict, user_confirmed: bool) -> dict:
    if user_confirmed is not True:
        return {"status": "rejected", "error": "user_confirmed must be true before submission."}

    # Never trust the LLM's earlier validate_requirements call as the sole
    # gate — re-validate server-side here too.
    validation = validate_requirements(resource_type, requirements)
    if not validation.get("valid"):
        return {"status": "invalid", "errors": validation.get("errors", [])}

    normalized = validation["normalized_requirements"]
    settings = get_settings()
    mode = settings.submit_requirements_mode

    if mode == "stub":
        logger.info(
            "SUBMIT_REQUIREMENTS (stub) resource_type=%s requirements=%s",
            resource_type,
            normalized,
        )
        return {"status": "received_stub", "resource_type": resource_type, "requirements": normalized}

    rendered_files = render_resource(resource_type, normalized, settings)
    slug = compute_slug(resource_type, normalized)

    if mode == "render_only":
        output_dir = settings.rendered_output_dir / slug
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in rendered_files.items():
            (output_dir / filename).write_text(content, encoding="utf-8")
        logger.info("SUBMIT_REQUIREMENTS (render_only) wrote %s", output_dir)
        return {"status": "rendered", "output_dir": str(output_dir), "files": list(rendered_files)}

    # mode == "full_pr"
    from app.submission.github_client import GitHubClient  # deferred: only needs GITHUB_TOKEN here

    client = GitHubClient(settings)
    result = client.submit_infra_request(resource_type, slug, rendered_files, normalized)
    logger.info("SUBMIT_REQUIREMENTS (full_pr) opened %s", result["pr_url"])
    return {"status": "pr_opened", **result}
