import json

from app.llm import orchestrator


class FakeFunction:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, call_id: str, name: str, arguments: dict):
        self.id = call_id
        self.function = FakeFunction(name, json.dumps(arguments))


class FakeMessage:
    def __init__(self, content: str | None = None, tool_calls: list[FakeToolCall] | None = None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none: bool = True) -> dict:
        data = {"role": "assistant", "content": self.content, "tool_calls": self.tool_calls}
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}
        return data


class FakeChoice:
    def __init__(self, message: FakeMessage):
        self.message = message


class FakeCompletion:
    def __init__(self, message: FakeMessage):
        self.choices = [FakeChoice(message)]


def test_run_turn_executes_tool_call_then_returns_final_reply(monkeypatch):
    responses = [
        FakeCompletion(
            FakeMessage(
                tool_calls=[FakeToolCall("call_1", "get_resource_schema", {"resource_type": "azure_sql_database"})]
            )
        ),
        FakeCompletion(FakeMessage(content="Which edition would you like?")),
    ]

    def fake_create_completion(messages):
        return responses.pop(0)

    dispatched = []

    def fake_dispatch(name, args):
        dispatched.append((name, args))
        return {"resource_type": "azure_sql_database", "required_fields": {}}

    monkeypatch.setattr(orchestrator, "create_completion", fake_create_completion)
    monkeypatch.setattr(orchestrator, "dispatch", fake_dispatch)

    reply, messages, followups = orchestrator.run_turn(
        [{"role": "system", "content": "sys"}], "I need an Azure SQL database"
    )

    assert reply == "Which edition would you like?"
    assert dispatched == [("get_resource_schema", {"resource_type": "azure_sql_database"})]
    assert any(m.get("role") == "tool" for m in messages)
    assert followups  # get_resource_schema isn't tracked, so falls back to the default suggestions


def test_run_turn_stops_at_max_iterations(monkeypatch):
    def fake_create_completion(messages):
        return FakeCompletion(
            FakeMessage(tool_calls=[FakeToolCall("call_x", "get_resource_schema", {"resource_type": "x"})])
        )

    monkeypatch.setattr(orchestrator, "create_completion", fake_create_completion)
    monkeypatch.setattr(orchestrator, "dispatch", lambda name, args: {})

    reply, _messages, _followups = orchestrator.run_turn([{"role": "system", "content": "sys"}], "hello")

    assert "stuck" in reply.lower()
