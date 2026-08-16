import json

from app.llm.followups import derive_followups


def _assistant_tool_call(call_id: str, name: str) -> dict:
    return {
        "role": "assistant",
        "tool_calls": [{"id": call_id, "function": {"name": name}}],
    }


def _tool_result(call_id: str, result: dict) -> dict:
    return {"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)}


def test_defaults_when_no_relevant_tool_call_yet():
    messages = [{"role": "user", "content": "hi"}]

    assert derive_followups(messages) == [
        "What Azure resources can you help me provision?",
        "What information will you need from me?",
    ]


def test_missing_required_fields_suggests_asking_whats_left():
    messages = [
        _assistant_tool_call("c1", "validate_requirements"),
        _tool_result("c1", {"valid": False, "errors": ["Missing required field: region"]}),
    ]

    followups = derive_followups(messages)

    assert "What fields are still missing?" in followups


def test_invalid_value_suggests_valid_options():
    messages = [
        _assistant_tool_call("c1", "validate_requirements"),
        _tool_result("c1", {"valid": False, "errors": ["region: 'x' is not a valid option."]}),
    ]

    followups = derive_followups(messages)

    assert "What are valid options for this field?" in followups


def test_valid_requirements_suggests_confirm_and_submit():
    messages = [
        _assistant_tool_call("c1", "validate_requirements"),
        _tool_result("c1", {"valid": True, "normalized_requirements": {}}),
    ]

    followups = derive_followups(messages)

    assert "Confirm and submit" in followups


def test_rendered_submission_suggests_showing_terraform():
    messages = [
        _assistant_tool_call("c1", "submit_requirements"),
        _tool_result("c1", {"status": "rendered", "output_dir": "x"}),
    ]

    assert derive_followups(messages) == ["Show me the generated Terraform", "Start a new request"]


def test_pr_opened_suggests_showing_the_pr():
    messages = [
        _assistant_tool_call("c1", "submit_requirements"),
        _tool_result("c1", {"status": "pr_opened", "pr_url": "https://example.com/pr/1"}),
    ]

    assert derive_followups(messages) == ["Show me the pull request", "Start a new request"]


def test_uses_most_recent_relevant_tool_result():
    messages = [
        _assistant_tool_call("c1", "validate_requirements"),
        _tool_result("c1", {"valid": False, "errors": ["Missing required field: region"]}),
        _assistant_tool_call("c2", "validate_requirements"),
        _tool_result("c2", {"valid": True, "normalized_requirements": {}}),
    ]

    assert "Confirm and submit" in derive_followups(messages)
