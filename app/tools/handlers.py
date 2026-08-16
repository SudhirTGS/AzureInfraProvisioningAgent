"""Single dispatch seam between the orchestrator's tool-calling loop and the
concrete tool implementations. Easy to unit test (call `dispatch` directly
with fixed args) and easy to mock in orchestrator tests.
"""

from collections.abc import Callable
from typing import Any

from app.submission.submit_handler import submit_requirements
from app.tools.schema_loader import get_resource_schema
from app.tools.validators import validate_field, validate_requirements

_REGISTRY: dict[str, Callable[..., dict]] = {
    "get_resource_schema": lambda args: get_resource_schema(args["resource_type"]),
    "validate_field": lambda args: validate_field(
        args["resource_type"], args["field_name"], args["value"]
    ),
    "validate_requirements": lambda args: validate_requirements(
        args["resource_type"], args["requirements"]
    ),
    "submit_requirements": lambda args: submit_requirements(
        args["resource_type"], args["requirements"], args.get("user_confirmed", False)
    ),
}


def dispatch(name: str, args: dict[str, Any]) -> dict:
    handler = _REGISTRY.get(name)
    if handler is None:
        return {"error": f"Unknown tool '{name}'."}
    try:
        return handler(args)
    except KeyError as exc:
        return {"error": f"Missing required argument {exc} for tool '{name}'."}
