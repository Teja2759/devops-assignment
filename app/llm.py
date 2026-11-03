import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()


def is_offline_mode() -> bool:
    return os.getenv("LLM_MODE", "auto").strip().lower() == "offline"


@lru_cache(maxsize=1)
def get_llm():
    if is_offline_mode():
        raise RuntimeError("LLM_MODE=offline; no external model is configured")
    return init_chat_model(
        os.getenv("LLM_MODEL", "claude-haiku-5-5"),
        model_provider=os.getenv("LLM_PROVIDER", "anthropic"),
        temperature=0,
        max_tokens=4096,
    )


def ask_tool(
    tool: dict[str, Any], system: str, user: str, *, tool_choice: str
) -> dict[str, Any]:
    """Call the model with a required structured tool and return its arguments."""
    reply = get_llm().bind_tools([tool], tool_choice=tool_choice).invoke(
        [("system", system), ("human", user)]
    )
    for call in reply.tool_calls:
        if call.get("name") == tool["name"]:
            return call["args"]
    raise ValueError(f"LLM did not return the required {tool['name']} tool call")


def format_pages(pages: list[dict]) -> str:
    return "\n\n".join(f"=== PAGE {p['page']} ===\n{p['text']}" for p in pages)
