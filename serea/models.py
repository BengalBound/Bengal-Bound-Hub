from django.db import models
from django.conf import settings
from workspace_admin.models import HiredAIEmployee
from encrypted_model_fields.fields import EncryptedCharField
from simple_history.models import HistoricalRecords
from .encryption import EncryptedTextField


class SereaAgent(models.Model):
    TIER_CHOICES = (
        ('intern', 'Intern (Entry Level)'),
        ('entry', 'Junior (1-3 yrs experience)'),
        ('mid', 'Mid-Level (3-5 yrs experience)'),
        ('senior', 'Senior (5+ yrs experience)'),
    )
    STATUS_CHOICES = (
        ('idle', 'Idle'),
        ('working', 'Working'),
        ('waiting', 'Waiting for Permission'),
        ('offline', 'Offline'),
    )

    # Supported AI models Serea can use
    AI_MODEL_CHOICES = (
        # ── NeuroLinkIt — Conversational (recommended for Serea) ──────────────
        # Best for social media, customer service, and community management
        ('neurolinkit/neural-chat:latest',                  'Neural Chat (NeuroLinkIt) — best for chat'),
        ('neurolinkit/unbound-neural-chat:latest',          'Neural Chat Unbound (NeuroLinkIt)'),
        ('neurolinkit/dolphin-mistral:7b',                  'Dolphin Mistral 7B (NeuroLinkIt) — best for persona'),
        ('neurolinkit/unbound-dolphin-mistral:7b',          'Dolphin Mistral 7B Unbound (NeuroLinkIt)'),
        # ── NeuroLinkIt — Strong General Reasoning ────────────────────────────
        ('neurolinkit/glm4:9b',                             'GLM4 9B (NeuroLinkIt) — strong general'),
        ('neurolinkit/unbound-glm4:latest',                 'GLM4 Unbound (NeuroLinkIt)'),
        ('neurolinkit/qwen2.5-coder:14b',                   'Qwen 2.5 14B (NeuroLinkIt) — strong reasoning'),
        ('neurolinkit/qwen2.5-coder:7b',                    'Qwen 2.5 7B (NeuroLinkIt)'),
        ('neurolinkit/unbound-qwen-coder:latest',           'Qwen Coder Unbound (NeuroLinkIt)'),
        ('neurolinkit/deepseek-coder-v2:16b',               'DeepSeek V2 16B (NeuroLinkIt) — most capable'),
        ('neurolinkit/unbound-deepseek-coder:latest',       'DeepSeek Coder Unbound (NeuroLinkIt)'),
        # ── NeuroLinkIt — Fast / Compact ──────────────────────────────────────
        ('neurolinkit/phi4-mini:latest',                    'Phi-4 Mini (NeuroLinkIt)'),
        ('neurolinkit/unbound-phi4-mini:latest',            'Phi-4 Mini Unbound (NeuroLinkIt)'),
        ('neurolinkit/phi3.5:latest',                       'Phi 3.5 (NeuroLinkIt)'),
        ('neurolinkit/unbound-phi3.5:latest',               'Phi 3.5 Unbound (NeuroLinkIt)'),
        ('neurolinkit/llama3.2:3b',                         'Llama 3.2 3B (NeuroLinkIt)'),
        ('neurolinkit/unbound-llama3.2:3b',                 'Llama 3.2 3B Unbound (NeuroLinkIt)'),
        ('neurolinkit/gemma3:1b',                           'Gemma 3 1B (NeuroLinkIt)'),
        ('neurolinkit/unbound-gemma3:1b',                   'Gemma 3 1B Unbound (NeuroLinkIt)'),
        ('neurolinkit/gemma2:2b',                           'Gemma 2 2B (NeuroLinkIt)'),
        ('neurolinkit/unbound-gemma2:2b',                   'Gemma 2 2B Unbound (NeuroLinkIt)'),
        ('neurolinkit/qwen3.5:0.8b',                        'Qwen 3.5 0.8B (NeuroLinkIt) — fastest'),
        ('neurolinkit/unbound-qwen3.5:0.8b',                'Qwen 3.5 0.8B Unbound (NeuroLinkIt)'),
        # ── NeuroLinkIt — Code-Specialized (available but less ideal for social media) ──
        ('neurolinkit/deepseek-coder-v2:16b-lite-instruct-q4_K_M', 'DeepSeek V2 16B Lite Q4 (NeuroLinkIt)'),
        ('neurolinkit/codellama:7b-python',                 'Code Llama 7B Python (NeuroLinkIt)'),
        ('neurolinkit/unbound-codellama-python:latest',     'Code Llama Python Unbound (NeuroLinkIt)'),
        # ── Groq — hosted cloud inference (fast, free tier) ───────────────────
        ('llama3-70b-8192',                         'Llama 3 70B (Groq)'),
        ('llama3-8b-8192',                          'Llama 3 8B (Groq)'),
        ('llama-3.3-70b-versatile',                 'Llama 3.3 70B Versatile (Groq)'),
        ('llama-3.1-8b-instant',                    'Llama 3.1 8B Instant (Groq)'),
        ('mixtral-8x7b-32768',                      'Mixtral 8×7B (Groq)'),
        ('gemma2-9b-it',                            'Gemma 2 9B (Groq)'),
        # ── OpenRouter — FREE models ──────────────────────────────────────────
        ('meta-llama/llama-3.3-70b-instruct:free',  'Llama 3.3 70B (OpenRouter FREE)'),
        ('meta-llama/llama-3.1-8b-instruct:free',   'Llama 3.1 8B (OpenRouter FREE)'),
        ('google/gemma-3-27b-it:free',              'Gemma 3 27B (OpenRouter FREE)'),
        ('mistralai/mistral-7b-instruct:free',      'Mistral 7B (OpenRouter FREE)'),
        ('deepseek/deepseek-r1:free',               'DeepSeek R1 (OpenRouter FREE)'),
        ('microsoft/phi-4:free',                    'Phi-4 (OpenRouter FREE)'),
        # ── OpenRouter — Paid models ──────────────────────────────────────────
        ('meta-llama/llama-3.3-70b-instruct',       'Llama 3.3 70B (OpenRouter)'),
        ('anthropic/claude-3.5-haiku',              'Claude 3.5 Haiku (OpenRouter)'),
        ('google/gemini-flash-1.5',                 'Gemini Flash 1.5 (OpenRouter)'),
        # ── OpenAI ────────────────────────────────────────────────────────────
        ('gpt-4o',                                  'GPT-4o (OpenAI)'),
        ('gpt-4o-mini',                             'GPT-4o Mini (OpenAI)'),
        ('gpt-3.5-turbo',                           'GPT-3.5 Turbo (OpenAI)'),
    )

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='serea_agents',
        help_text="The Client owning this agent."
    )
    # Optional 1-to-1 link to an existing HiredAIEmployee record
    hired_employee = models.OneToOneField(
        HiredAIEmployee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='serea_agent'
    )

    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='intern')

    PERSONA_CHOICES = (
        ('serea', 'Serea (Default Virtual Assistant)'),
        ('aelin', 'Aelin (Female AI Employee)'),
        ('kael', 'Kael (Male AI Employee)'),
    )
    persona = models.CharField(
        max_length=20,
        choices=PERSONA_CHOICES,
        default='serea',
        help_text="The visual and communication persona the AI will adopt."
    )

    neurolinkit_api_key = EncryptedCharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="API key for NeuroLinkIt (own AI server). Falls back to NEUROLINKIT_API_KEY env var."
    )
    groq_api_key = EncryptedCharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional per-client Groq API key. Falls back to the platform GROQ_API_KEY env var."
    )
    openai_api_key = EncryptedCharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional per-client OpenAI API key. Required when using an OpenAI model."
    )
    openrouter_api_key = EncryptedCharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional per-client OpenRouter API key. Falls back to OPENROUTER_API_KEY env var."
    )
    ai_model = models.CharField(
        max_length=80,
        choices=AI_MODEL_CHOICES,
        default='neurolinkit/neural-chat:latest',
        help_text=(
            "The LLM model Serea will use. "
            "NeuroLinkIt models run on your home server (configure NEUROLINKIT_BASE_URL). "
            "Recommended for social media: Neural Chat, Dolphin Mistral, or GLM4."
        )
    )
    managed_platforms = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Platforms this agent actively monitors and moderates. "
            "Options: facebook, instagram, linkedin. "
            "Empty = manage all connected platforms. "
            "Example: [\"facebook\", \"instagram\"]"
        )
    )
    token_limit_override = models.IntegerField(
        null=True,
        blank=True,
        help_text=(
            "Monthly token cap for this agent. "
            "Leave blank to inherit the cap from the hired AI tier. "
            "Set to 0 for unlimited."
        )
    )
    tokens_used_this_month = models.IntegerField(
        default=0,
        help_text="Running total of tokens consumed this calendar month."
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    onboarding_complete = models.BooleanField(
        default=False,
        help_text="True once the client has connected at least one platform and provided content."
    )

    # Employee relationship fields — make Serea feel like a real team member
    manager_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Who Serea reports to. She'll address this person when escalating or asking for approval."
    )
    working_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start of Serea's working day (your local time). Leave blank for 24/7."
    )
    working_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End of Serea's working day (your local time). Leave blank for 24/7."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Serea Agent'
        verbose_name_plural = 'Serea Agents'

    def __str__(self):
        return f"Serea ({self.get_tier_display()}) — {self.tenant.email}"


class AgentInstruction(models.Model):
    """
    Runtime behaviour rules for a specific SereaAgent instance.
    Unlike AITrainingDocument (long-form context), these are short, active directives
    injected directly into Serea's system prompt on every invocation.
    e.g. "Always sign off with 'Best, Serea'" or "Never delete comments; flag instead."
    """
    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='instructions')
    instruction_text = models.TextField(
        help_text='Short directive, e.g. "Always use emojis and sign off with \'Best, Serea\'"'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agent Instruction'
        verbose_name_plural = 'Agent Instructions'

    def __str__(self):
        return f"Instruction for {self.agent}: {self.instruction_text[:50]}"


class ConversationMessage(models.Model):
    """
    Slack-style chat history between the client and Serea inside console_admin.
    Extends the basic AIChatInteraction with human-in-the-loop permission fields.
    """
    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='messages')
    # 'serea' or the client's email address
    sender = models.CharField(max_length=150, help_text="'serea' or client email")
    message_text = models.TextField()

    # Human-in-the-loop fields
    is_permission_request = models.BooleanField(
        default=False,
        help_text="True when Serea's confidence < 0.7 and she needs the client to approve an action."
    )
    permission_granted = models.BooleanField(
        null=True,
        blank=True,
        help_text="Null = pending, True = approved, False = denied."
    )
    # Stores the pending action context so the Celery task can resume it
    pending_action_context = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON payload describing the action awaiting human approval."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conversation Message'
        verbose_name_plural = 'Conversation Messages'
        ordering = ['created_at']

    def __str__(self):
        flag = ' [PERMISSION REQUEST]' if self.is_permission_request else ''
        return f"{self.sender} @ {self.created_at.strftime('%Y-%m-%d %H:%M')}{flag}"


class ModerationLog(models.Model):
    ACTION_CHOICES = (
        ('delete', 'Delete'),
        ('reply', 'Reply'),
        ('flag', 'Flag'),
        ('ignore', 'Ignore'),
        ('pending_approval', 'Pending Approval'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='moderation_logs')
    platform = models.CharField(max_length=50, help_text="e.g. Facebook, Instagram, X (Twitter)")
    comment_text = models.TextField()
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES)

    sentiment_score = models.FloatField(
        help_text="0.0 (negative) → 1.0 (positive)",
        null=True,
        blank=True
    )
    confidence_score = models.FloatField(
        help_text="Serea's confidence in this decision (0.0 → 1.0)",
        null=True,
        blank=True
    )

    # Links back to the ConversationMessage if human approval was needed
    permission_message = models.OneToOneField(
        ConversationMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_log'
    )
    requires_human = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Moderation Log'
        verbose_name_plural = 'Moderation Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.agent.get_tier_display()}] {self.action_taken.upper()}: {self.comment_text[:40]}..."


class ContentQueue(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('posted', 'Posted'),
        ('failed', 'Failed'),
    )

    PLATFORM_CHOICES = (
        ('Instagram', 'Instagram'),
        ('Facebook', 'Facebook'),
        ('Twitter', 'X (Twitter)'),
        ('LinkedIn', 'LinkedIn'),
        ('TikTok', 'TikTok'),
        ('YouTube', 'YouTube'),
        ('Other', 'Other'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='content_queue')
    title = models.CharField(max_length=255)
    platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES,
        default='Instagram',
        help_text="Target social media platform."
    )
    caption = models.TextField(
        blank=True,
        default='',
        help_text="Post caption / body text written by Serea or the client."
    )
    hashtags = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Space or comma-separated hashtags (e.g. #brand #sale)."
    )

    sheet_link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Google Sheet URL containing post metadata (caption, hashtags, target platform, etc.)"
    )
    drive_link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Google Drive URL for the image or video asset to post."
    )

    platform_post_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Post ID / URN returned by the platform API after publishing."
    )
    media_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Public URL of the image or video asset for this post."
    )

    post_date = models.DateTimeField(help_text="Scheduled UTC post time")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_detail = models.TextField(
        blank=True,
        null=True,
        help_text="Populated if status='failed'; contains the error message for debugging."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Content Queue Item'
        verbose_name_plural = 'Content Queue'
        ordering = ['post_date']

    def __str__(self):
        return f"[{self.platform}] {self.title} @ {self.post_date.strftime('%Y-%m-%d %H:%M')} [{self.status}]"


class SereaReport(models.Model):
    """
    Stores reports generated by Serea on demand or automatically.
    Clients can view these in the console chat or admin panel.
    """
    REPORT_TYPES = (
        ('daily',      'Daily Briefing'),
        ('weekly',     'Weekly Summary'),
        ('moderation', 'Moderation Report'),
        ('content',    'Content Report'),
        ('custom',     'Custom Report'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='custom')
    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Full report content generated by Serea.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Serea Report'
        verbose_name_plural = 'Serea Reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()}: {self.title} ({self.created_at.date()})"


class SocialMediaAccount(models.Model):
    """
    Stores the client's social media platform credentials for a SereaAgent.
    Serea uses these to post content, monitor comments, and reply to DMs.

    Each agent can have at most one account per platform (unique_together).
    In production, access_token and extra_credentials MUST be encrypted at rest.
    """
    PLATFORM_CHOICES = (
        ('facebook',   'Facebook'),
        ('instagram',  'Instagram'),
        ('tiktok',     'TikTok'),
        ('whatsapp',   'WhatsApp Business'),
        ('twitter_x',  'X (Twitter)'),
        ('youtube',    'YouTube'),
        # LinkedIn removed — not supported for posting; kept for display only
        ('linkedin',   'LinkedIn (view-only)'),
    )

    # Platforms that have a real posting adapter implemented
    POSTING_PLATFORMS = ('facebook', 'instagram', 'tiktok')
    STATUS_CHOICES = (
        ('connected', 'Connected'),
        ('error',     'Connection Error'),
        ('expired',   'Token Expired'),
    )

    # Platform-specific help text shown in the connection form
    PLATFORM_INSTRUCTIONS = {
        'facebook': (
            'Go to developers.facebook.com → My Apps → Graph API Explorer. '
            'Select your Page, generate a Page Access Token, and paste it here. '
            'Account ID = your Facebook Page ID (found in About section of your Page).'
        ),
        'instagram': (
            'Instagram is managed via the Facebook Graph API. '
            'Connect your Facebook account first, then provide the Instagram Business Account ID '
            '(found in your Instagram Business settings → About → Account ID) '
            'and a Page Access Token from your linked Facebook Page.'
        ),
        'whatsapp': (
            'Go to developers.facebook.com → WhatsApp → API Setup. '
            'Copy the Temporary Access Token and Phone Number ID. '
            'Account ID = WhatsApp Business Account (WABA) ID from your Business Manager.'
        ),
        'twitter_x': (
            'Go to developer.twitter.com → Your App → Keys and Tokens. '
            'You need: API Key, API Key Secret, Access Token, and Access Token Secret. '
            'Paste the Access Token here. Put API Key and API Secret in the extra fields.'
        ),
        'tiktok': (
            'Go to developers.tiktok.com → your app → Auth code. '
            'Complete the OAuth flow to get an Access Token and Open ID. '
            'Paste Access Token here; put Open ID in the extra credentials field.'
        ),
        'linkedin': (
            'Go to LinkedIn Developer Portal (developer.linkedin.com) → Create App. '
            'Add products: "Share on LinkedIn" and "Sign In with LinkedIn using OpenID Connect". '
            'Generate an Access Token via OAuth 2.0 (3-legged flow). '
            'Your Organization ID is the number in your company page URL: '
            'linkedin.com/company/<organization_id>/admin/. '
            'Required scopes: w_organization_social, r_organization_social, r_1st_connections_size.'
        ),
        'youtube': (
            'Use Google OAuth2 to get an Access Token and Refresh Token for the '
            'YouTube Data API v3 scope. Channel ID is found in YouTube Studio → Settings → Channel → Advanced.'
        ),
    }

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    account_id = models.CharField(
        max_length=255,
        help_text="Page ID / Account ID / Channel ID on the platform"
    )
    account_name = models.CharField(
        max_length=255,
        help_text="Your page name or @handle as it appears on the platform"
    )
    access_token = EncryptedTextField(
        help_text="Primary access token. Encrypted at rest. Do not share."
    )
    extra_credentials = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Platform-specific extra credentials as JSON. Examples:\n"
            "Twitter: {\"api_key\": \"...\", \"api_secret\": \"...\", \"access_token_secret\": \"...\"}\n"
            "Instagram: {\"instagram_business_account_id\": \"...\"}\n"
            "WhatsApp: {\"phone_number_id\": \"...\", \"waba_id\": \"...\"}\n"
            "YouTube: {\"refresh_token\": \"...\", \"channel_id\": \"...\"}"
        )
    )

    # Learned page info (populated by Serea after connecting)
    page_bio = models.TextField(blank=True, default='', help_text="Bio / description fetched from the platform")
    page_data = models.JSONField(
        default=dict, blank=True,
        help_text="Cached metadata fetched from the platform API (followers, category, etc.)"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='connected')
    last_error = models.TextField(blank=True, null=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp of the last comment-fetch run by monitor_social_task."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('agent', 'platform')
        verbose_name = 'Social Media Account'
        verbose_name_plural = 'Social Media Accounts'
        ordering = ['platform']

    def __str__(self):
        return f"{self.get_platform_display()} — {self.account_name}"

    def get_summary(self) -> str:
        """Short one-line summary for injection into Serea's prompt."""
        bio_snippet = f': "{self.page_bio[:80]}"' if self.page_bio else ''
        return f"{self.get_platform_display()} (@{self.account_name}, ID={self.account_id}){bio_snippet}"


class ClientContentFile(models.Model):
    """
    Business knowledge files provided by the client for Serea to learn from.
    Serea uses these to answer DMs, write contextually accurate posts,
    know what tone to use, and understand what comments to keep or delete.

    Sources:
      • CSV upload  — client uploads a .csv with Q&A, product info, etc.
      • Manual text — client pastes content directly
      • Google Drive — link to a Drive folder/doc Serea can access via her tool
    """
    SOURCE_CHOICES = (
        ('csv_upload',   'CSV File Upload'),
        ('manual_text',  'Manual Text Entry'),
        ('google_drive', 'Google Drive Link'),
    )
    CONTENT_TYPE_CHOICES = (
        ('product_info',         'Product / Service Info'),
        ('faq',                  'FAQ (Frequently Asked Questions)'),
        ('tone_guide',           'Tone & Voice Guide'),
        ('brand_guidelines',     'Brand Guidelines'),
        ('response_templates',   'Response Templates for Comments/DMs'),
        ('competitor_info',      'Competitor Research'),
        ('post_content',         'Posts / Content for Publishing'),
        ('other',                'Other'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='content_files')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='', help_text="What is this content for?")
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual_text')
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPE_CHOICES, default='other')

    # Content sources (only one applies per record)
    file = models.FileField(
        upload_to='serea/content/',
        null=True, blank=True,
        help_text="Upload a .csv or .txt file"
    )
    drive_url = models.URLField(
        max_length=500, blank=True, null=True,
        help_text="Google Drive folder or file URL"
    )
    manual_text = models.TextField(
        blank=True, default='',
        help_text="Paste your content directly here (Markdown supported)"
    )

    # Auto-extracted text (populated when file is saved)
    parsed_content = models.TextField(
        blank=True, default='',
        help_text="Extracted/cleaned text content injected into Serea's context"
    )

    is_active = models.BooleanField(default=True, help_text="Only active files are used by Serea")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Content File'
        verbose_name_plural = 'Content Files'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_content_type_display()}] {self.title}"

    def get_content_for_injection(self) -> str:
        """Returns the best available content string for Serea's context."""
        if self.parsed_content:
            return self.parsed_content
        if self.manual_text:
            return self.manual_text
        if self.drive_url:
            return f"[Google Drive content — use the interact_with_drive tool: {self.drive_url}]"
        return ''


class SereaTask(models.Model):
    """
    A task assigned to Serea by the client — directly from chat or the Tasks panel.
    Unlike AITask (which requires a project), SereaTask is lightweight and
    is the primary way clients delegate work to their AI employee.

    Clients assign tasks, Serea updates them as she works, and posts back
    in chat when done. If she needs info or approval she sets the appropriate status.
    """
    PRIORITY_CHOICES = (
        ('low',    'Low'),
        ('normal', 'Normal'),
        ('high',   'High'),
        ('urgent', 'Urgent — drop everything'),
    )
    STATUS_CHOICES = (
        ('todo',              'To Do'),
        ('in_progress',       'In Progress'),
        ('waiting_approval',  'Waiting for Your Approval'),
        ('waiting_info',      'Waiting for More Info'),
        ('done',              'Done'),
        ('cancelled',         'Cancelled'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='serea_tasks')
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    due_date = models.DateTimeField(null=True, blank=True)

    # Serea's running notes / progress update on this task
    progress_notes = models.TextField(
        blank=True, default='',
        help_text="Serea's working notes — updated as she makes progress"
    )
    result = models.TextField(
        blank=True, default='',
        help_text="Serea's final output or summary when the task is done"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Serea Task'
        verbose_name_plural = 'Serea Tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"

    def is_active(self) -> bool:
        return self.status in ('todo', 'in_progress', 'waiting_approval', 'waiting_info')


class DailyReport(models.Model):
    """
    A structured end-of-day report generated by Serea.
    Clients review each item, flag anything wrong, then send feedback back to Serea.
    Clients can also fix issues manually or reassign tasks.
    """
    STATUS_CHOICES = (
        ('pending',    'Pending Review'),
        ('reviewed',   'Reviewed'),
        ('approved',   'Approved'),
        ('has_issues', 'Has Issues — Serea is fixing'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='daily_reports')
    report_date = models.DateField()
    summary = models.TextField(blank=True, help_text="Serea's narrative end-of-day summary")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    generated_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_reports'
    )
    client_feedback = models.TextField(blank=True, default='')
    feedback_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('agent', 'report_date')
        ordering = ['-report_date']
        verbose_name = 'Daily Report'
        verbose_name_plural = 'Daily Reports'

    def __str__(self):
        return f"Daily Report — {self.report_date} [{self.get_status_display()}]"

    @property
    def flagged_count(self):
        return self.items.filter(is_flagged=True).count()


class DailyReportItem(models.Model):
    """
    A single line item inside a DailyReport.
    Clients can flag individual items as wrong, add a reason,
    and choose whether to reassign to Serea or mark as manually fixed.
    """
    ITEM_TYPE_CHOICES = (
        ('task',       'Task'),
        ('post',       'Post Scheduled/Published'),
        ('moderation', 'Moderation Action'),
        ('dm',         'DM / Comment Reply'),
        ('general',    'General Update'),
    )
    OUTCOME_CHOICES = (
        ('completed',        'Completed'),
        ('in_progress',      'In Progress'),
        ('waiting_approval', 'Waiting for Approval'),
        ('failed',           'Failed'),
        ('skipped',          'Skipped'),
    )
    CLIENT_ACTION_CHOICES = (
        ('none',          'No Action'),
        ('reassign',      'Reassign to Serea'),
        ('fixed_manually','Fixed Manually'),
    )

    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='general')
    title = models.CharField(max_length=255)
    detail = models.TextField(blank=True, default='')
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='completed')
    linked_task = models.ForeignKey(
        'SereaTask', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='report_items'
    )
    # Client review fields
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True, default='')
    client_action = models.CharField(max_length=20, choices=CLIENT_ACTION_CHOICES, default='none')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Daily Report Item'
        verbose_name_plural = 'Daily Report Items'

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.title}"


class CampaignTracker(models.Model):
    """
    Tracks social media campaigns — product launches, promotions, events.
    Serea creates and updates these as she plans and executes campaigns.
    """
    STATUS_CHOICES = (
        ('planning',   'Planning'),
        ('active',     'Active'),
        ('paused',     'Paused'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    platforms = models.JSONField(
        default=list,
        help_text="Platforms this campaign runs on. E.g. [\"facebook\", \"instagram\", \"linkedin\"]"
    )
    goal = models.TextField(
        blank=True, default='',
        help_text="Campaign objective — e.g. 'Increase followers by 20%', 'Drive 500 link clicks'"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    progress_notes = models.TextField(blank=True, default='', help_text="Serea's running notes on campaign progress")
    results_summary = models.TextField(blank=True, default='', help_text="Final results when campaign ends")
    hashtags = models.CharField(max_length=500, blank=True, default='', help_text="Campaign-specific hashtags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.name}"


class EngagementLog(models.Model):
    """
    Logs individual engagement actions taken by Serea on social media:
    liking posts, following accounts, replying to comments, etc.
    Used to track Serea's outreach activity and prevent over-engagement.
    """
    ACTION_CHOICES = (
        ('like',          'Liked a Post'),
        ('comment',       'Commented on a Post'),
        ('follow',        'Followed an Account'),
        ('unfollow',      'Unfollowed an Account'),
        ('share',         'Shared / Reposted'),
        ('dm_sent',       'Sent a DM'),
        ('mention_reply', 'Replied to Mention'),
        ('story_react',   'Reacted to Story'),
        ('poll_vote',     'Voted in Poll'),
        ('other',         'Other'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='engagement_logs')
    platform = models.CharField(max_length=20)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_account = models.CharField(
        max_length=255, blank=True, default='',
        help_text="The account or post targeted by this action"
    )
    target_url = models.URLField(max_length=500, blank=True, null=True)
    notes = models.TextField(blank=True, default='', help_text="Why Serea took this action")
    campaign = models.ForeignKey(
        CampaignTracker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='engagement_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Engagement Log'
        verbose_name_plural = 'Engagement Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.platform}] {self.get_action_display()} → {self.target_account or 'unknown'}"


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY
# ─────────────────────────────────────────────────────────────────────────────

class SereaMemory(models.Model):
    """
    Serea's persistent working memory — things she remembers about users,
    situations, community patterns, and anything the employer taught her.

    Injected automatically into her system prompt so she never forgets context
    across separate Celery runs or chat sessions.
    """
    MEMORY_TYPES = (
        ('user',      'Platform User Note'),
        ('brand',     'Brand Voice / Policy Note'),
        ('community', 'Community Situation'),
        ('customer',  'Customer Issue Note'),
        ('offender',  'Repeat Offender Record'),
        ('general',   'General Note'),
    )
    IMPORTANCE_CHOICES = (
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='memories')
    memory_type = models.CharField(max_length=20, choices=MEMORY_TYPES, default='general')
    subject = models.CharField(
        max_length=255,
        help_text="Who or what this memory is about. e.g. 'user:fb_12345', 'brand tone', 'PR situation May 2026'."
    )
    platform = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Platform this memory relates to (blank = all platforms)."
    )
    content = models.TextField(help_text="The actual memory — what Serea should remember.")
    importance = models.CharField(max_length=10, choices=IMPORTANCE_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Leave blank for a permanent memory. Set a date for time-limited context."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Serea Memory'
        verbose_name_plural = 'Serea Memories'
        ordering = ['-importance', '-created_at']

    def __str__(self):
        return f"[{self.get_memory_type_display()}] {self.subject[:60]}"


# ─────────────────────────────────────────────────────────────────────────────
# COMMUNITY MEMBER PROFILES
# ─────────────────────────────────────────────────────────────────────────────

class CommunityMemberProfile(models.Model):
    """
    Serea's knowledge of individual platform users — engagement history,
    violations, welcome status, and running notes.

    Used to identify repeat offenders, super-fans, and new members who
    haven't been welcomed yet.
    """
    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='community_members')
    platform = models.CharField(max_length=20)
    platform_user_id = models.CharField(max_length=255, help_text="The user's ID on the platform.")
    username = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, default='')
    welcomed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When Serea first welcomed this member."
    )
    engagement_score = models.FloatField(
        default=0.5,
        help_text="0.0 = bad actor / troll, 0.5 = neutral, 1.0 = brand advocate / loyal member."
    )
    violation_count = models.IntegerField(
        default=0,
        help_text="Number of rule violations Serea has recorded for this user."
    )
    is_flagged = models.BooleanField(
        default=False,
        help_text="True when this user is on watch — their activity gets extra scrutiny."
    )
    is_blocked = models.BooleanField(
        default=False,
        help_text="True when this user has been blocked / reported."
    )
    flag_reason = models.TextField(blank=True, default='')
    notes = models.TextField(
        blank=True, default='',
        help_text="Serea's running notes about this user — context for future interactions."
    )
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('agent', 'platform', 'platform_user_id')
        verbose_name = 'Community Member'
        verbose_name_plural = 'Community Members'
        ordering = ['-last_seen_at']

    def __str__(self):
        flags = ''
        if self.is_blocked:
            flags = ' [BLOCKED]'
        elif self.is_flagged:
            flags = ' [FLAGGED]'
        return f"[{self.platform}] @{self.username}{flags}"


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMER SERVICE THREADS
# ─────────────────────────────────────────────────────────────────────────────

class CustomerServiceThread(models.Model):
    """
    Tracks an ongoing customer service conversation — from first contact
    to resolution. Serea opens, updates, and closes these as she works.
    """
    STATUS_CHOICES = (
        ('open',             'Open'),
        ('in_progress',      'In Progress'),
        ('waiting_customer', 'Waiting on Customer'),
        ('escalated',        'Escalated'),
        ('resolved',         'Resolved'),
        ('closed',           'Closed'),
    )
    PRIORITY_CHOICES = (
        ('low',    'Low'),
        ('normal', 'Normal'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='cs_threads')
    platform = models.CharField(max_length=20)
    platform_thread_id = models.CharField(
        max_length=255, blank=True, default='',
        help_text="DM thread / conversation ID on the platform, if available."
    )
    customer_name = models.CharField(max_length=255)
    customer_platform_id = models.CharField(max_length=255, blank=True, default='')
    subject = models.CharField(max_length=255, help_text="One-line description of the issue.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    serea_notes = models.TextField(
        blank=True, default='',
        help_text="Serea's running notes on this thread — context, actions taken, next steps."
    )
    escalated_to = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Team or person this was escalated to."
    )
    resolution = models.TextField(blank=True, default='', help_text="How this was resolved.")
    opened_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'CS Thread'
        verbose_name_plural = 'CS Threads'
        ordering = ['-opened_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.customer_name} — {self.subject[:50]}"


# ─────────────────────────────────────────────────────────────────────────────
# ESCALATION RECORDS
# ─────────────────────────────────────────────────────────────────────────────

class EscalationRecord(models.Model):
    """
    Logs situations Serea identified as needing internal team escalation:
    PR crises, legal contacts, coordinated attacks, press enquiries, etc.
    """
    ESCALATION_TYPES = (
        ('pr_crisis',   'PR Crisis'),
        ('legal',       'Legal / Compliance'),
        ('technical',   'Technical Problem'),
        ('harassment',  'Serious Harassment / Abuse'),
        ('spam_attack', 'Coordinated Spam Attack'),
        ('media',       'Media / Press Enquiry'),
        ('regulator',   'Regulator / Government Contact'),
        ('other',       'Other'),
    )
    SEVERITY_CHOICES = (
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical — Act Now'),
    )
    STATUS_CHOICES = (
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
    )

    agent = models.ForeignKey(SereaAgent, on_delete=models.CASCADE, related_name='escalations')
    escalation_type = models.CharField(max_length=20, choices=ESCALATION_TYPES, default='other')
    description = models.TextField(help_text="What happened and why this needs escalating.")
    platform = models.CharField(max_length=20, blank=True, default='')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    escalated_to = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Team, department, or person this was escalated to."
    )
    resolution = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Escalation Record'
        verbose_name_plural = 'Escalation Records'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"[{self.get_severity_display().upper()}] "
            f"{self.get_escalation_type_display()} — {self.description[:60]}"
        )
