import json
import requests
from django.conf import settings
from .toolkit import UNIVERSAL_TOOLS, execute_tool

def agent_chat(messages: list, model: str = None) -> str:
    """
    Send messages to the LiteLLM proxy and return the assistant reply.
    This is the ONLY correct way to call any AI model in this project.
    Now equipped with the Universal Toolkit loop for internet/API access.
    """
    model = model or settings.SEREA_TASK_MODELS.get("chat", "neural-chat")
    
    # Inject tool awareness into the system prompt automatically
    messages_copy = list(messages)
    for m in messages_copy:
        if m.get("role") == "system":
            instruction = "\n\n[SYSTEM]: You are an autonomous AI. You have access to tools that can search the internet, scrape websites, and call APIs. Use them whenever you need real-time information or external data."
            if instruction not in m.get("content", ""):
                m["content"] += instruction
            break
            
    for _ in range(5):  # Max 5 tool iterations
        resp = requests.post(
            f"{settings.LITELLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"},
            json={"model": model, "messages": messages_copy, "tools": UNIVERSAL_TOOLS},
            timeout=45,
        )
        resp.raise_for_status()
        
        message = resp.json()["choices"][0]["message"]
        
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
                    "content": str(result)
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


