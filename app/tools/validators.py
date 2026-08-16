"""Hand-rolled, table-driven validation.

Deliberately not `jsonschema`-based: the one cross-field rule this schema
needs (service_objective depends on edition) doesn't map cleanly onto plain
JSON Schema without an if/then per enum value, and keeping everything in
ordinary Python control flow makes it easier to unit test and reason about.
"""

import re
from typing import Any

from app.tools.schema_loader import get_resource_schema

# Cross-field rule: service_objective's valid values depend on edition. Keyed
# by the *prefix* the service_objective string must start with for a given
# edition (Basic's service_objective is the literal string "Basic").
EDITION_SERVICE_OBJECTIVE_PREFIXES: dict[str, tuple[str, ...]] = {
    "Basic": ("Basic",),
    "Standard": ("S",),
    "GeneralPurpose": ("GP_",),
    "BusinessCritical": ("BC_",),
    "Hyperscale": ("HS_",),
}

# Cross-field rule: max_size_gb is capped by edition. Real Azure ceilings in
# GB (Basic's 2 GB cap is a hard limit; the others are simplified upper
# bounds — actual limits also vary by service_objective within an edition).
EDITION_MAX_SIZE_GB_LIMITS: dict[str, int] = {
    "Basic": 2,
    "Standard": 1024,
    "GeneralPurpose": 4096,
    "BusinessCritical": 4096,
    "Hyperscale": 102400,
}


def _find_field_def(schema: dict, field_name: str) -> dict | None:
    return schema.get("required_fields", {}).get(field_name) or schema.get(
        "optional_fields", {}
    ).get(field_name)


def _coerce_for_type(value: Any, expected_type: str) -> Any:
    """Tool-call arguments arrive as JSON, so ints/arrays may come through as
    strings from a chatty model. Coerce the obvious cases; anything else is
    left as-is and will fail the type check below with a clear error."""
    if expected_type == "integer" and isinstance(value, str) and value.lstrip("-").isdigit():
        return int(value)
    return value


def _validate_single_field(field_def: dict, value: Any) -> str | None:
    expected_type = field_def.get("type")
    value = _coerce_for_type(value, expected_type)

    if expected_type == "string" and not isinstance(value, str):
        return f"Expected a string, got {type(value).__name__}."
    if expected_type == "integer" and not isinstance(value, int):
        return f"Expected an integer, got {type(value).__name__}."
    if expected_type == "array" and not isinstance(value, list):
        return f"Expected an array, got {type(value).__name__}."

    enum = field_def.get("enum")
    if enum and value not in enum:
        return f"'{value}' is not a valid option."

    pattern = field_def.get("pattern")
    if pattern and isinstance(value, str) and not re.fullmatch(pattern, value):
        return f"'{value}' does not match the required format."

    return None


def validate_field(resource_type: str, field_name: str, value: Any) -> dict:
    """Tool-handler for `validate_field`."""
    schema = get_resource_schema(resource_type)
    if "error" in schema:
        return schema

    field_def = _find_field_def(schema, field_name)
    if field_def is None:
        return {"valid": False, "error": f"'{field_name}' is not a known field on {resource_type}."}

    error = _validate_single_field(field_def, value)
    if error is None:
        return {"valid": True}

    response: dict = {"valid": False, "error": error}
    if "enum" in field_def:
        response["valid_options"] = field_def["enum"]
    if "pattern" in field_def:
        response["expected_pattern"] = field_def["pattern"]
    return response


def _validate_edition_service_objective(requirements: dict) -> str | None:
    edition = requirements.get("edition")
    service_objective = requirements.get("service_objective")
    if not edition or not service_objective:
        return None
    prefixes = EDITION_SERVICE_OBJECTIVE_PREFIXES.get(edition)
    if prefixes is None:
        return None
    if not any(service_objective.startswith(p) for p in prefixes):
        return (
            f"service_objective '{service_objective}' is not valid for edition '{edition}'. "
            f"Expected it to start with one of: {', '.join(prefixes)}."
        )
    return None


def _validate_max_size_for_edition(requirements: dict) -> str | None:
    edition = requirements.get("edition")
    max_size_gb = requirements.get("max_size_gb")
    if not edition or max_size_gb is None:
        return None
    limit = EDITION_MAX_SIZE_GB_LIMITS.get(edition)
    if limit is not None and max_size_gb > limit:
        return f"max_size_gb {max_size_gb} exceeds the limit for edition '{edition}' ({limit} GB max)."
    return None


def validate_requirements(resource_type: str, requirements: dict) -> dict:
    """Tool-handler for `validate_requirements`. Checks every required field is
    present, validates every present field against the schema, cross-checks
    edition/service_objective, and on success fills in optional-field
    defaults into `normalized_requirements`."""
    schema = get_resource_schema(resource_type)
    if "error" in schema:
        return {"valid": False, "errors": [schema["error"]]}

    required_fields: dict = schema.get("required_fields", {})
    optional_fields: dict = schema.get("optional_fields", {})

    missing = [name for name in required_fields if requirements.get(name) in (None, "")]
    if missing:
        return {"valid": False, "errors": [f"Missing required field: {name}" for name in missing]}

    errors: list[str] = []
    for name, value in requirements.items():
        field_def = required_fields.get(name) or optional_fields.get(name)
        if field_def is None:
            errors.append(f"'{name}' is not a known field on {resource_type}.")
            continue
        error = _validate_single_field(field_def, value)
        if error:
            errors.append(f"{name}: {error}")

    cross_field_error = _validate_edition_service_objective(requirements)
    if cross_field_error:
        errors.append(cross_field_error)

    max_size_error = _validate_max_size_for_edition(requirements)
    if max_size_error:
        errors.append(max_size_error)

    if errors:
        return {"valid": False, "errors": errors}

    normalized = dict(requirements)
    for name, field_def in optional_fields.items():
        if name not in normalized and "default" in field_def:
            normalized[name] = field_def["default"]

    # The schema-wide max_size_gb default may exceed what the chosen edition
    # actually supports (e.g. Basic caps at 2 GB, not the general 32 GB
    # default) — cap it down rather than handing Terraform a value Azure will
    # reject at apply time.
    edition_limit = EDITION_MAX_SIZE_GB_LIMITS.get(normalized.get("edition"))
    if edition_limit is not None and normalized.get("max_size_gb", 0) > edition_limit:
        normalized["max_size_gb"] = edition_limit

    return {"valid": True, "normalized_requirements": normalized}
