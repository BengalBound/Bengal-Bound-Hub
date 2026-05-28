import requests
from django.conf import settings

def agent_chat(messages: list, model: str = None) -> str:
    """
    Send messages to the LiteLLM proxy and return the assistant reply.
    This is the ONLY correct way to call any AI model in this project.
    """
    model = model or settings.SEREA_TASK_MODELS.get("chat", "neural-chat")
    resp = requests.post(
        f"{settings.LITELLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"},
        json={"model": model, "messages": messages},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

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


