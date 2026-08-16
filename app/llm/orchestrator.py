"""The tool-calling loop.

Kept deterministic and easy to test: `run_turn` takes the prior message list
plus a new user message, drives the OpenAI client + tool dispatch loop, and
returns the final assistant reply along with the updated message list for the
caller to persist back into the session store.
"""

import json
import logging

from app.llm.client import create_completion
from app.llm.followups import derive_followups
from app.tools.handlers import dispatch

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 8


def run_turn(messages: list[dict], user_message: str) -> tuple[str, list[dict], list[str]]:
    messages = [*messages, {"role": "user", "content": user_message}]

    for _ in range(MAX_TOOL_ITERATIONS):
        completion = create_completion(messages)
        choice = completion.choices[0].message
        messages.append(choice.model_dump(exclude_none=True))

        if not choice.tool_calls:
            return choice.content or "", messages, derive_followups(messages)

        for tool_call in choice.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            logger.info("tool_call name=%s args=%s", name, args)
            result = dispatch(name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    logger.warning("MAX_TOOL_ITERATIONS reached without a final assistant reply")
    return (
        "Sorry, I got stuck working through that request. Could you rephrase or try again?",
        messages,
        derive_followups(messages),
    )
