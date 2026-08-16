"""Deterministic follow-up suggestions.

Derived from the most recent `validate_requirements` / `submit_requirements`
tool result already sitting in the message history — never from an extra LLM
call — so suggestions are free, consistent, and never invent Azure values the
user hasn't actually provided themselves.
"""

import json
from typing import Any

_RELEVANT_TOOLS = {"validate_requirements", "submit_requirements"}

_DEFAULT = [
    "What Azure resources can you help me provision?",
    "What information will you need from me?",
]


def _attr(obj: Any, name: str) -> Any:
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)


def _tool_call_names(messages: list[dict]) -> dict[str, str]:
    """Map tool_call_id -> function name by scanning prior assistant turns."""
    names: dict[str, str] = {}
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for tool_call in message.get("tool_calls") or []:
            call_id = _attr(tool_call, "id")
            function = _attr(tool_call, "function")
            name = _attr(function, "name")
            if call_id and name:
                names[call_id] = name
    return names


def derive_followups(messages: list[dict]) -> list[str]:
    names = _tool_call_names(messages)

    for message in reversed(messages):
        if message.get("role") != "tool":
            continue
        name = names.get(message.get("tool_call_id"))
        if name not in _RELEVANT_TOOLS:
            continue
        try:
            result = json.loads(message.get("content") or "{}")
        except json.JSONDecodeError:
            continue
        return _followups_for(name, result)

    return list(_DEFAULT)


def _followups_for(tool_name: str, result: dict) -> list[str]:
    if tool_name == "submit_requirements":
        return _followups_for_submission(result)
    return _followups_for_validation(result)


def _followups_for_submission(result: dict) -> list[str]:
    status = result.get("status")
    if status == "rendered":
        return ["Show me the generated Terraform", "Start a new request"]
    if status == "pr_opened":
        return ["Show me the pull request", "Start a new request"]
    if status == "received_stub":
        return ["Start a new request"]
    if status in ("invalid", "rejected"):
        return ["What needs to change?", "Show me what I've provided so far"]
    return list(_DEFAULT)


def _followups_for_validation(result: dict) -> list[str]:
    if result.get("valid"):
        return ["Show me a summary before I confirm", "Change a field", "Confirm and submit"]

    errors = result.get("errors") or []
    if any(e.lower().startswith("missing required field") for e in errors):
        return ["What fields are still missing?", "Show me what I've provided so far"]
    return ["What are valid options for this field?", "Show me what I've provided so far"]
