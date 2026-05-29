import logging
from agents.models import Agent
from organizations.models import Organization

logger = logging.getLogger(__name__)

class AgentProvisioningService:
    """
    Handles the auto-provisioning of AI employees for a new workspace.
    """

    @staticmethod
    def spawn_default_roster(organization: Organization) -> None:
        """
        Spawns the default agents (Concierge and Inspector) for the given organization.
        """

        # 1. Concierge - Customer Support & Intake
        concierge_prompt = (
            f"You are the Concierge for {organization.name}, operating in the {organization.industry} industry. "
            "Your primary role is to act as the frontline receptionist, greet users or clients, answer FAQs, "
            "and route complex queries to human operators. Always maintain a professional and welcoming tone."
        )

        Agent.objects.create(
            organization=organization,
            name="Concierge",
            role="Customer Support",
            system_prompt=concierge_prompt,
            model_override="gemini/gemini-1.5-flash" # Default to fast model for basic interaction
        )

        # 2. Inspector - Compliance & Security
        inspector_prompt = (
            f"You are the Inspector for {organization.name}. Your duty is fail-closed security and compliance. "
            f"You must evaluate all incoming requests against regional compliance standards for {organization.country_code}. "
            "If an action poses a data breach risk or violates standard operating procedure, you must block it."
        )

        Agent.objects.create(
            organization=organization,
            name="Inspector",
            role="Compliance Officer",
            system_prompt=inspector_prompt,
            model_override="gemini/gemini-1.5-flash" # Use fast model for realtime request checking
        )

        # 3. Serea - Content Strategy & Campaigns
        serea_prompt = (
            f"You are Serea, the Content Strategist for {organization.name}, "
            f"operating in the {organization.industry} industry. "
            "Your expertise is copywriting, email campaign drafting, and generating brand-aligned "
            "content across blog posts, social media, and advertising copy. "
            "Always match the organisation's tone and target audience."
        )

        Agent.objects.create(
            organization=organization,
            name="Serea",
            role="Content Strategist",
            system_prompt=serea_prompt,
            model_override="gemini/gemini-1.5-pro",
        )

        logger.info(f"Successfully spawned default Agent roster for organization: {organization.name}")
