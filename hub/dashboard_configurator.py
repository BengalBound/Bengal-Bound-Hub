import json
import logging
import re
from django.conf import settings
from agents.utils import agent_chat
from hub.models import DashboardConfig, TenantModule, ModuleCatalog
from workspace_admin.models import HiredAIEmployee, Subscription, AIEmployeeTier
from agents.models import AgentCatalog

logger = logging.getLogger(__name__)

class DashboardConfigurator:
    """
    Takes client's 6 answers -> configures their entire Bengal Bound workspace.
    Powered by LiteLLM proxy (LITELLM_BASE_URL) (reasoning model).
    """

    BUSINESS_AGENT_MAP = {
        "ecommerce":     ["merch", "concierge", "serea-content", "flux"],
        "agency":        ["lead-hunter", "content-architect", "oracle", "reporting-bot"],
        "clinic":        ["medibook", "concierge", "hera", "sage"],
        "restaurant":    ["concierge", "serea-content", "cash", "tempo"],
        "real_estate":   ["realt", "concierge", "lead-hunter", "sage"],
        "consulting":    ["lead-hunter", "atlas", "reporting-bot", "sage"],
        "manufacturing": ["payload", "flux", "hera", "atlas"],
    }

    CHALLENGE_AGENT_MAP = {
        "getting_leads":       ["concierge", "lead-hunter", "serea-content"],
        "social_media":        ["serea-content", "content-architect", "luma"],
        "customer_support":    ["shield", "concierge"],
        "hr_payroll":          ["hera", "tempo"],
        "finance_invoicing":   ["cash", "sage"],
        "project_management":  ["atlas", "reporting-bot", "nova"],
    }

    THEME_MAP = {
        "agency":        {"primary": "#4F46E5", "accent": "#06B6D4", "theme": "agency"},
        "clinic":        {"primary": "#10B981", "accent": "#3B82F6", "theme": "clinic"},
        "ecommerce":     {"primary": "#F97316", "accent": "#8B5CF6", "theme": "ecommerce"},
        "restaurant":    {"primary": "#EF4444", "accent": "#F59E0B", "theme": "restaurant"},
        "real_estate":   {"primary": "#1E40AF", "accent": "#D97706", "theme": "real_estate"},
        "consulting":    {"primary": "#475569", "accent": "#14B8A6", "theme": "consulting"},
        "manufacturing": {"primary": "#374151", "accent": "#F97316", "theme": "manufacturing"},
    }

    def configure(self, business, answers: dict, custom_agents=None, agent_tiers=None) -> DashboardConfig:
        # 1. Select recommended agents
        biz_type = answers.get('business_type', 'other')
        challenge = answers.get('main_challenge', 'getting_leads')

        if custom_agents is not None:
            recommended = custom_agents
        else:
            business_agents = self.BUSINESS_AGENT_MAP.get(biz_type, [])
            challenge_agents = self.CHALLENGE_AGENT_MAP.get(challenge, [])

            # Deduplicate + rank by relevance
            recommended = []
            for a in business_agents + challenge_agents:
                if a not in recommended:
                    recommended.append(a)
            recommended = recommended[:5]

        # 2. AI generates personalised dashboard layout
        layout = self.ai_generate_layout(answers, recommended)

        # 3. Set language, currency, payment method
        lang = answers.get('language', 'English')
        payment = answers.get('payment_preference', 'Stripe')
        
        # Simple local mapping for GeoService simulation
        currency = 'USD'
        if payment == 'bKash' or lang == 'বাংলা':
            currency = 'BDT'

        theme_info = self.THEME_MAP.get(biz_type, {"primary": "#63DCB8", "accent": "#6366F1", "theme": "default"})

        config, _ = DashboardConfig.objects.update_or_create(
            business=business,
            defaults={
                'recommended_agents': recommended,
                'layout': layout,
                'language': lang,
                'currency': currency,
                'payment_method': payment,
                'dashboard_theme': theme_info['theme'],
                'primary_color': theme_info['primary'],
                'is_configured': True,
            }
        )

        # 4. Auto-hire custom agents or first recommended agent on free Intern tier
        if custom_agents is not None:
            for agent_slug in custom_agents:
                tier_name = 'intern'
                if agent_tiers and agent_slug in agent_tiers:
                    tier_name = agent_tiers[agent_slug]
                self.activate_starter_agent(business, agent_slug, tier_name)
        else:
            if recommended:
                self.activate_starter_agent(business, recommended[0], 'intern')

        return config

    def ai_generate_layout(self, answers: dict, agents: list) -> dict:
        """LiteLLM proxy decides the best dashboard layout for this client"""
        prompt = f"""
        A {answers.get('business_type', 'other')} business with {answers.get('team_size', 'Just me')} people
        is setting up Bengal Bound. Their main challenge is {answers.get('main_challenge', 'getting_leads')}.
        They use: {answers.get('platforms', [])}.
        Recommended agents: {agents}

        Design their dashboard layout:
        - Which widgets to show first (most relevant metrics)
        - Widget order and prominence
        - Quick action buttons
        - What data to show in each section

        Respond ONLY as valid JSON matching this schema:
        {{
            "widgets": [
                {{"id": "modules_grid", "title": "Installed Modules", "size": "large", "order": 1}},
                {{"id": "ai_chat", "title": "AI Employee", "size": "medium", "order": 2}},
                {{"id": "quick_actions", "title": "Quick Actions", "size": "small", "order": 3}}
            ],
            "layout": "standard_grid",
            "primary_color_suggestion": "#63DCB8"
        }}
        Choose from these valid widget IDs: "modules_grid", "ai_chat", "quick_actions", "business_info".
        Do not wrap the JSON in markdown code blocks.
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            model = settings.SEREA_TASK_MODELS.get('analysis', 'qwen2.5-coder')
            response_text = agent_chat(messages, model=model)
            
            # Extract JSON if LLM returned markdown
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(response_text.strip())
        except Exception as e:
            logger.error(f"Failed to generate layout via LLM: {e}")
            # Fallback layout
            return {
                "widgets": [
                    {"id": "modules_grid", "title": "Installed Modules", "size": "large", "order": 1},
                    {"id": "ai_chat", "title": "AI Employee", "size": "medium", "order": 2},
                    {"id": "quick_actions", "title": "Quick Actions", "size": "small", "order": 3}
                ],
                "layout": "standard_grid",
                "primary_color_suggestion": "#63DCB8"
            }

    def activate_starter_agent(self, business, agent_slug, tier_name='intern'):
        try:
            agent_catalog = AgentCatalog.objects.get(slug=agent_slug, is_active=True)
            
            # Ensure custom or default tier exists
            try:
                tier = AIEmployeeTier.objects.get(name=tier_name)
            except AIEmployeeTier.DoesNotExist:
                tier, _ = AIEmployeeTier.objects.get_or_create(
                    name=tier_name,
                    defaults={
                        'description': f'{tier_name.title()} Level',
                        'token_limit': 1000000,
                        'monthly_price_usd': 0.00 if tier_name == 'intern' else 10.00,
                        'role': 'general'
                    }
                )

            owner = business.owner
            if not HiredAIEmployee.objects.filter(employer=owner, agent_catalog=agent_catalog, is_active=True).exists():
                new_ai = HiredAIEmployee.objects.create(
                    employer=owner,
                    tier=tier,
                    agent_catalog=agent_catalog,
                    ai_name=agent_catalog.name
                )
                
                # Active subscription
                from django.utils import timezone
                from datetime import timedelta
                Subscription.objects.get_or_create(
                    client=owner,
                    hired_ai=new_ai,
                    defaults={
                        'tier': tier,
                        'billing_cycle': 'monthly',
                        'status': 'active',
                        'amount_paid_usd': 0.00,
                        'started_at': timezone.now(),
                        'current_period_end': timezone.now() + timedelta(days=365*10)
                    }
                )
        except Exception as e:
            logger.error(f"Failed to activate starter agent {agent_slug} with tier {tier_name}: {e}")


class DashboardAIModifier:
    """
    Client asks AI to change their dashboard in natural language.
    All changes validated by Inspector (simulated or explicit layout constraints).
    """

    ALLOWED_MODIFICATIONS = [
        "widget_order", "theme_color", "language",
        "notification_settings", "agent_config",
        "dashboard_layout", "hide_widget", "show_widget",
        "rename_workspace", "update_timezone"
    ]

    def modify(self, business, natural_language_request: str) -> dict:
        try:
            config = DashboardConfig.objects.get(business=business)
        except DashboardConfig.DoesNotExist:
            return {"success": False, "message": "Dashboard configuration not found."}

        prompt = f"""
        The user wants to modify their dashboard layout or theme styling.
        Their request: "{natural_language_request}"

        Current Layout JSON: {json.dumps(config.layout)}
        Current Theme: {config.dashboard_theme}
        Current Primary Color: {config.primary_color}

        Allowed Modifications: {self.ALLOWED_MODIFICATIONS}

        Interpret the request and respond strictly with a JSON object containing:
        - layout: updated layout JSON with the requested widgets order/presence (ensure it follows the widgets array structure of {{id, title, size, order}})
        - theme: updated theme if changed (agency, clinic, ecommerce, restaurant, real_estate, consulting, manufacturing, default)
        - primary_color: updated primary color hex code if changed
        - message: a friendly message confirming what changes were made

        Do not wrap response in markdown code blocks. Ensure it is valid JSON.
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            model = settings.SEREA_TASK_MODELS.get('analysis', 'qwen2.5-coder')
            response_text = agent_chat(messages, model=model)
            
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                parsed = json.loads(response_text.strip())

            # Update the configuration
            if "layout" in parsed and parsed["layout"]:
                config.layout = parsed["layout"]
            if "theme" in parsed and parsed["theme"]:
                config.dashboard_theme = parsed["theme"]
            if "primary_color" in parsed and parsed["primary_color"]:
                config.primary_color = parsed["primary_color"]
            
            config.save()
            return {"success": True, "message": parsed.get("message", "Dashboard updated successfully.")}
        except Exception as e:
            logger.error(f"Failed to modify dashboard via LLM: {e}")
            return {"success": False, "message": f"Could not process dashboard modifications: {str(e)}"}
