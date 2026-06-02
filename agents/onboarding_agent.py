import json
import logging
from django.conf import settings
from .utils import get_llm

logger = logging.getLogger(__name__)

def get_onboarding_chat_response(messages: list) -> dict:
    """
    Sends a message to the Onboarding Solutions Architect LLM.
    Returns a dict with 'reply' (the text for the user) and optionally 'cart_update' (a parsed dict).
    """
    system_prompt = """You are a helpful Solutions Architect for BengalBound, an AI-powered business OS.
The user is on the onboarding checkout page. They are looking at a list of available Modules and AI Agents.
Your job is to ask them what their business does, and recommend modules or AI Agent tiers based on their needs.

Available Modules to recommend (use exactly these IDs):
- crm (Customer Relationship Management)
- invoicing (Invoicing & Billing)
- pos (Point of Sale)
- inventory (Inventory & Stock)
- hr (Human Resources & Attendance)
- payroll (Payroll processing)
- task_board (Task Management)
- ecommerce (Online Store)
- documents (Document Management)
- business_calendar (Calendar & Booking)
- delivery (Delivery & Logistics)

Available AI Employee Tiers:
- intern (Free, very basic tasks)
- entry (Standard, handles most basic moderation/chat)
- mid (Advanced workflows and reasoning)
- senior (Expert level, complex autonomy)

When you recommend modules or a new AI tier, you MUST include a special tag at the very end of your response so the frontend can automatically update their shopping cart checkboxes.
Format it exactly like this:

<CART_UPDATE>
{"add_modules": ["pos", "inventory"], "remove_modules": [], "ai_tier": "entry"}
</CART_UPDATE>

Only include the tag if you are actually recommending a change to their cart. Keep your responses concise, friendly, and helpful. Do not mention pricing details unless asked, focus on capabilities.
"""
    
    # We will use the same LLM logic as the rest of the app, but via Langchain's direct invoke for simplicity
    llm = get_llm()
    
    # Langchain expects a specific format or we can use litellm directly.
    # Since get_llm returns a Langchain BaseChatModel, we invoke it with BaseMessages.
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
            
    try:
        result = llm.invoke(lc_messages)
        full_reply = result.content
        
        # Parse out the <CART_UPDATE> tag
        cart_update = None
        display_text = full_reply
        
        if "<CART_UPDATE>" in full_reply and "</CART_UPDATE>" in full_reply:
            start = full_reply.find("<CART_UPDATE>") + len("<CART_UPDATE>")
            end = full_reply.find("</CART_UPDATE>")
            json_str = full_reply[start:end].strip()
            
            # Clean up the display text to remove the tag
            display_text = full_reply.replace(full_reply[full_reply.find("<CART_UPDATE>"):full_reply.find("</CART_UPDATE>")+len("</CART_UPDATE>")], "").strip()
            
            try:
                cart_update = json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse CART_UPDATE JSON: {json_str}")
        
        return {
            "reply": display_text,
            "cart_update": cart_update
        }
        
    except Exception as exc:
        logger.error(f"Onboarding agent failed: {exc}", exc_info=True)
        return {
            "reply": "I'm having trouble connecting to my systems right now. You can continue selecting modules manually on the left!",
            "cart_update": None
        }
