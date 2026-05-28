# AI-Configured Client Dashboard
# Bengal Bound — "Your Dashboard, Built by AI, for You"
# BengalBound Ltd | v1.0

---

## Concept: Zero-Config Onboarding

When a client signs up, instead of a blank dashboard —
**AI interviews them and builds their perfect workspace in 3 minutes.**

```
Step 1: Client passes KYB (Veritas)
Step 2: AI asks 6 questions about their business
Step 3: AI configures their entire dashboard, agents, and payment
Step 4: Client arrives at a dashboard that feels like it was built for them
Step 5: Client can modify anything by just asking the AI
```

---

## The 6-Question AI Onboarding Interview

```
┌──────────────────────────────────────────────────────────────────┐
│  Welcome to Bengal Bound! Let's set up your AI team.                   │
│  6 quick questions → ready in 3 minutes.                         │
│                                                                   │
│  1. "What type of business do you run?"                          │
│     [E-commerce] [Agency] [Clinic] [Restaurant] [Real Estate]   │
│     [Consulting] [Manufacturing] [Other: _______________]        │
│                                                                   │
│  2. "What's your biggest challenge right now?"                   │
│     [Getting more leads] [Managing social media]                 │
│     [Customer support] [HR & payroll] [Finance & invoicing]      │
│     [Managing projects] [Multiple of these]                      │
│                                                                   │
│  3. "How many people are in your team?"                          │
│     [Just me] [2–5] [6–20] [21–100] [100+]                      │
│                                                                   │
│  4. "Which platforms do you use?" (select all)                   │
│     [WhatsApp Business] [Facebook/Instagram] [Gmail/Outlook]     │
│     [Shopify/WooCommerce] [Google Ads/Meta Ads] [None yet]       │
│                                                                   │
│  5. "What's your preferred language?"                            │
│     [English] [বাংলা] [العربية] [हिंदी] [Other]                  │
│                                                                   │
│  6. "How would you like to pay?"                                 │
│     [bKash] [Card (Visa/MC)] [Stripe] [Crypto] [Bank Transfer]  │
│                                                                   │
│                          [Build My AI Team →]                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## AI Dashboard Configuration Engine

```python
class DashboardConfigurator:
    """
    Takes client's 6 answers → configures their entire Bengal Bound workspace
    Powered by LiteLLM proxy (LITELLM_BASE_URL) (reasoning model)
    """

    BUSINESS_AGENT_MAP = {
        "ecommerce":    ["Merch", "Concierge", "Iris", "Serea", "Flux"],
        "agency":       ["Lead Hunter", "Content Architect", "Serea", "Oracle", "Reporting Bot"],
        "clinic":       ["MediBook", "Concierge", "Hera", "Sage"],
        "restaurant":   ["Concierge", "Serea", "Cash", "Tempo"],
        "real_estate":  ["Realt", "Concierge", "Lead Hunter", "Sage"],
        "consulting":   ["Lead Hunter", "Iris", "Atlas", "Reporting Bot", "Sage"],
        "manufacturing":["Payload", "Flux", "Finn", "Hera", "Atlas"],
    }

    CHALLENGE_AGENT_MAP = {
        "getting_leads":       ["Concierge", "Lead Hunter", "Serea"],
        "social_media":        ["Serea", "Content Architect", "Luma"],
        "customer_support":    ["Shield", "Iris", "Concierge"],
        "hr_payroll":          ["Hera", "Tempo", "Finn"],
        "finance_invoicing":   ["Finn", "Cash", "Sage"],
        "project_management":  ["Atlas", "Reporting Bot", "Nova"],
    }

    def configure(self, answers: dict, client_id: str) -> DashboardConfig:
        # 1. Select recommended agents
        business_agents = self.BUSINESS_AGENT_MAP.get(
            answers['business_type'], [])
        challenge_agents = self.CHALLENGE_AGENT_MAP.get(
            answers['main_challenge'], [])

        # Deduplicate + rank by relevance
        recommended = list(set(business_agents + challenge_agents))[:5]

        # 2. AI generates personalised dashboard layout
        layout = self.ai_generate_layout(answers, recommended)

        # 3. Set language, currency, payment method
        config = DashboardConfig(
            client_id=client_id,
            recommended_agents=recommended,
            layout=layout,
            language=answers['language'],
            currency=GeoService.get_currency(answers['country']),
            payment_method=answers['payment_preference'],
            dashboard_theme=self.get_theme(answers['business_type'])
        )

        # 4. Auto-hire first agent on free Intern tier
        self.activate_starter_agent(recommended[0], client_id)

        return config

    def ai_generate_layout(self, answers: dict, agents: list) -> dict:
        """LiteLLM proxy decides the best dashboard layout for this client"""
        prompt = f"""
        A {answers['business_type']} business with {answers['team_size']} people
        is setting up Bengal Bound. Their main challenge is {answers['main_challenge']}.
        They use: {answers['platforms']}.

        Design their dashboard layout:
        - Which widgets to show first (most relevant metrics)
        - Widget order and prominence
        - Quick action buttons
        - What data to show in each section

        Respond as JSON with: widgets[], layout, primary_color_suggestion
        """
        return AIEngine.generate_structured(prompt, schema=DashboardLayout)
```

---

## AI Dashboard Modifier ("Change Anything by Asking")

After setup, clients can modify their dashboard by just asking:

```
Client types: "Move my analytics chart to the top"
→ AI updates dashboard layout JSON
→ Inspector checks (layout change = no compliance concern)
→ Dashboard refreshes instantly

Client types: "I want my dashboard to look more professional, use dark blue"
→ AI updates theme_primary_color to #1E3A5F
→ Regenerates CSS tokens for client's workspace
→ Applied instantly

Client types: "Add a widget for today's WhatsApp messages"
→ AI adds WhatsApp message count widget
→ If Concierge active: widget shows real data
→ If not hired: widget shows "Hire Concierge" CTA

Client types: "Remove the social media section, I don't need it"
→ AI hides Serea-related widgets
→ Dashboard reorganises automatically
```

```python
class DashboardAIModifier:
    """
    Client asks AI to change their dashboard in natural language
    All changes validated by Inspector before applying
    """

    ALLOWED_MODIFICATIONS = [
        "widget_order", "theme_color", "language",
        "notification_settings", "agent_config",
        "dashboard_layout", "hide_widget", "show_widget",
        "rename_workspace", "update_timezone"
    ]

    def modify(self, client_id: str, natural_language_request: str):
        # 1. AI interprets the request
        modification = AIEngine.parse_modification(
            request=natural_language_request,
            current_config=self.get_config(client_id),
            allowed_modifications=self.ALLOWED_MODIFICATIONS
        )

        # 2. Inspector validates (within SRS boundaries)
        result = Inspector.evaluate(
            action=modification,
            client_id=client_id
        )

        if result.approved:
            self.apply_modification(client_id, modification)
            self.notify_user("Dashboard updated ✅", client_id)
        else:
            self.notify_user(
                f"Cannot apply: {result.reason}. "
                f"Here's what you can do instead: {result.alternative}",
                client_id
            )
```

---

## Payment Flow (Integrated in Dashboard)

```
Client on dashboard → sees "Upgrade to Mid tier"
      │
      ▼
One-click payment sheet slides up (bottom sheet on mobile)
      │
      ├── Bangladesh: [bKash] [Nagad] [Card]
      ├── India: [UPI] [Cards] [Net Banking]
      ├── UAE: [Card] [Apple Pay]
      ├── Global: [Card] [Crypto] [PayPal]
      │
Client selects method → pays → tier activated instantly
      │
      ▼
Dashboard refreshes → new agents unlocked
Finn auto-generates invoice → Iris emails to client
```

---

## Per-Client Customisation Boundaries (SRS Guardrails)

Clients CAN change:
- ✅ Dashboard layout and widget order
- ✅ Theme colour (from approved palette)
- ✅ Language and timezone
- ✅ Agent configuration and knowledge base
- ✅ Notification preferences
- ✅ Team member roles and permissions
- ✅ Payment methods and billing details

Clients CANNOT change (Inspector enforces):
- ❌ Data retention policies (set by law/Bengal Bound TOS)
- ❌ Compliance rules (Inspector is immutable)
- ❌ Audit log contents (append-only, immutable)
- ❌ Access to other clients' data (row-level security)
- ❌ AI model used (Bengal Bound controls this, not clients)
- ❌ Inspector gate bypass (no override possible)

---

## Dashboard Themes by Business Type

| Business Type | Primary Colour | Accent | Personality |
|---|---|---|---|
| Agency | Indigo `#4F46E5` | Cyan `#06B6D4` | Creative, bold |
| Clinic | Green `#10B981` | Blue `#3B82F6` | Clean, trustworthy |
| E-commerce | Orange `#F97316` | Purple `#8B5CF6` | Energetic, vibrant |
| Restaurant | Red `#EF4444` | Amber `#F59E0B` | Warm, appetising |
| Real Estate | Navy `#1E40AF` | Gold `#D97706` | Premium, established |
| Consulting | Slate `#475569` | Teal `#14B8A6` | Professional, sharp |
| Manufacturing | Steel `#374151` | Orange `#F97316` | Industrial, reliable |
| Default (Bengal Bound) | Teal `#63DCB8` | Indigo `#6366F1` | Modern, intelligent |

---

*BengalBound Ltd — AI Dashboard Configuration v1.0*
*"Every client gets a dashboard that feels like it was built just for them."*
