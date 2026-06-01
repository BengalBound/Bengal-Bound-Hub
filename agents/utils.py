"""
All AI calls go through this module — LangChain 1.x (LangGraph) only.
Never call Groq, OpenAI, or any provider directly outside this file.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _use_proxy() -> bool:
    url = getattr(settings, "LITELLM_BASE_URL", "")
    return bool(url) and "localhost" not in url and "127.0.0.1" not in url


def get_llm(model: str = None):
    """Return the appropriate LangChain chat model for the current environment."""
    if _use_proxy():
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url=f"{settings.LITELLM_BASE_URL}/v1",
            api_key=settings.LITELLM_MASTER_KEY,
            model=model or settings.SEREA_TASK_MODELS.get("chat", "neural-chat"),
            timeout=45,
        )
    from langchain_groq import ChatGroq
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        timeout=45,
    )


def agent_chat(
    messages: list,
    model: str = None,
    business=None,
    agent_slug: str = None,
) -> str:
    """
    Run a conversation through a LangChain / LangGraph agent with tools.

    Args:
        messages:    OpenAI-format list [{"role": ..., "content": ...}]
        model:       Optional LLM model override
        business:    BusinessInstance — enables hub data tools when provided
        agent_slug:  Catalog slug — selects the correct subset of hub tools
    """
    from langchain.agents import create_agent
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from .toolkit import get_universal_tools

    # --- Parse the OpenAI-format message list ---
    lc_messages = []
    system_content = (
        "You are a helpful AI employee for a business. "
        "Use your tools whenever you need real-time or business-specific data."
    )
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content") or ""
        if role == "system":
            system_content = content
        elif role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    # --- Assemble tools ---
    tools = get_universal_tools()
    if business is not None:
        try:
            from .hub_tools import get_hub_tools
            tools = tools + get_hub_tools(business, agent_slug=agent_slug)
        except Exception as exc:
            logger.warning("hub_tools load failed (%s/%s): %s", business, agent_slug, exc)

    # --- Build and run the LangGraph agent ---
    llm = get_llm(model)
    agent = create_agent(llm, tools, system_prompt=system_content)

    try:
        result = agent.invoke({"messages": lc_messages})
        # result["messages"] is a list; the last message is the final AI reply
        final = result["messages"][-1]
        return getattr(final, "content", str(final))
    except Exception as exc:
        logger.error("agent_chat failed: %s", exc, exc_info=True)
        return f"Error: {exc}"


def ai_chat(system_prompt: str, messages: list, _organization_id=None, **kwargs) -> str:
    """Backward-compatibility shim for Serea-era callers."""
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)
    return agent_chat(messages=full_messages)


class AuditLog:
    """Stub preventing import errors when the compliance module is not installed."""
    class MockManager:
        @staticmethod
        def create(*args, **kwargs):
            return None
    objects = MockManager()
