"""Generic resource-schema discovery and loading.

Adding a new resource type is "drop a `<resource_type>.json` file into
`schemas/`" — nothing here is hardcoded to `azure_sql_database`.
"""

import json
from functools import lru_cache

from app.config import get_settings


class SchemaNotFoundError(Exception):
    pass


def list_available_resource_types() -> list[str]:
    schemas_dir = get_settings().schemas_dir
    if not schemas_dir.exists():
        return []
    return sorted(p.stem for p in schemas_dir.glob("*.json"))


@lru_cache
def load_schema(resource_type: str) -> dict:
    schemas_dir = get_settings().schemas_dir
    path = schemas_dir / f"{resource_type}.json"
    if not path.exists():
        raise SchemaNotFoundError(resource_type)
    return json.loads(path.read_text(encoding="utf-8"))


def get_resource_schema(resource_type: str) -> dict:
    """Tool-handler for `get_resource_schema`. Never raises — on an unknown
    resource type it returns an error payload so the LLM can tell the user
    plainly what's supported instead of inventing a schema."""
    try:
        return load_schema(resource_type)
    except SchemaNotFoundError:
        supported = list_available_resource_types()
        return {
            "error": f"Unsupported resource type '{resource_type}'.",
            "supported_resource_types": supported,
        }
