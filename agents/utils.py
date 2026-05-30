import json
import requests
from django.conf import settings

# Maps the internal model nicknames → real Groq model IDs used by litellm library
_GROQ_MODEL_MAP = {
    "neural-chat":             "groq/meta-llama/llama-4-scout-17b-16e-instruct",  # 30k TPM
    "dolphin-mistral":         "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "glm4":                    "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen2.5-coder":           "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "phi4-mini":               "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "gemini/gemini-1.5-flash": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
}


def _call_via_proxy(messages_copy, model, tools):
    """HTTP call to the LiteLLM proxy server."""
    resp = requests.post(
        f"{settings.LITELLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"},
        json={"model": model, "messages": messages_copy, "tools": tools},
        timeout=45,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]


def _call_via_library(messages_copy, model, tools):
    """Direct litellm library call — works without a proxy server running."""
    import litellm
    groq_model = _GROQ_MODEL_MAP.get(model, "groq/llama-3.1-8b-instant")
    response = litellm.completion(
        model=groq_model,
        messages=messages_copy,
        tools=tools or None,
        api_key=settings.GROQ_API_KEY,
        timeout=45,
    )
    msg = response.choices[0].message
    # Normalise to plain dict so the rest of the code works unchanged
    return {
        "role": "assistant",
        "content": msg.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in (msg.tool_calls or [])
        ] or None,
    }


def _use_proxy() -> bool:
    """True when a proxy URL is configured AND it is not localhost (proxy must be running)."""
    url = getattr(settings, "LITELLM_BASE_URL", "")
    return bool(url) and "localhost" not in url and "127.0.0.1" not in url


def agent_chat(messages: list, model: str = None) -> str:
    """
    Send messages through LiteLLM and return the assistant reply.
    - If LITELLM_BASE_URL points to a remote proxy: uses the HTTP proxy.
    - Otherwise (localhost / not set): calls the litellm Python library directly
      using GROQ_API_KEY — no separate proxy process required.
    """
    from .toolkit import UNIVERSAL_TOOLS, execute_tool  # lazy — avoids startup curl_cffi load

    model = model or settings.SEREA_TASK_MODELS.get("chat", "neural-chat")

    messages_copy = list(messages)
    for m in messages_copy:
        if m.get("role") == "system":
            instruction = (
                "\n\n[SYSTEM]: You are an autonomous AI. You have access to tools "
                "that can search the internet, scrape websites, and call APIs. "
                "Use them whenever you need real-time information or external data."
            )
            if instruction not in m.get("content", ""):
                m["content"] += instruction
            break

    call = _call_via_proxy if _use_proxy() else _call_via_library

    for _ in range(5):
        message = call(messages_copy, model, UNIVERSAL_TOOLS)

        if message.get("tool_calls"):
            messages_copy.append(message)
            for tc in message["tool_calls"]:
                tool_name = tc["function"]["name"]
                try:
                    arguments = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}
                result = execute_tool(tool_name, arguments)
                messages_copy.append({
                    "role": "tool",
                    "name": tool_name,
                    "tool_call_id": tc["id"],
                    "content": str(result),
                })
        else:
            return message.get("content", "")

    return "Error: Exceeded maximum tool call iterations."

def ai_chat(system_prompt: str, messages: list, organization_id=None, **kwargs) -> str:
    """
    Backward-compatibility wrapper translating comparison's ai_chat parameters
    to unified agent_chat calls.
    """
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)
    return agent_chat(messages=full_messages, model="gemini/gemini-1.5-flash")

class AuditLog:
    """
    Mock class for compliance AuditLog to prevent import errors and allow
    clean execution of view logs when the compliance module is not installed.
    """
    class MockManager:
        @staticmethod
        def create(*args, **kwargs):
            return None
    objects = MockManager()


