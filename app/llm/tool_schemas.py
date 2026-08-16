"""OpenAI function-calling tool schemas.

Shapes match the design spec verbatim: get_resource_schema, validate_field,
validate_requirements, submit_requirements.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_resource_schema",
            "description": (
                "Retrieve the required and optional fields, valid enums, and validation "
                "rules for a given Azure resource type. Always call this before asking the "
                "user for any field on a resource type you haven't already fetched the "
                "schema for."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "description": "e.g. 'azure_sql_database', 'storage_account', 'app_service'",
                    }
                },
                "required": ["resource_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_field",
            "description": (
                "Validate a single field value against the resource schema's rules "
                "(type, enum, pattern). Use this when a user-supplied value is ambiguous "
                "or looks like it might be invalid."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string"},
                    "field_name": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["resource_type", "field_name", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_requirements",
            "description": (
                "Validate the full collected requirements object against the schema for "
                "this resource type. Call this once all required fields appear to be "
                "collected, before summarizing for user confirmation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string"},
                    "requirements": {
                        "type": "object",
                        "description": "All collected key-value pairs for this resource.",
                    },
                },
                "required": ["resource_type", "requirements"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_requirements",
            "description": (
                "Final submission of a user-confirmed, fully validated requirements object. "
                "Only call this after the user has explicitly confirmed the summarized "
                "parameters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string"},
                    "requirements": {"type": "object"},
                    "user_confirmed": {"type": "boolean"},
                },
                "required": ["resource_type", "requirements", "user_confirmed"],
            },
        },
    },
]
