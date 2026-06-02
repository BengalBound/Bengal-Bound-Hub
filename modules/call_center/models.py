from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TwilioConfig(models.Model):
    business = models.OneToOneField(
        'bredbound.BusinessInstance', on_delete=models.CASCADE,
        related_name='twilio_config'
    )
    account_sid = models.CharField(max_length=64, blank=True)
    auth_token = models.CharField(max_length=64, blank=True, help_text='Master Auth Token — used only to validate Twilio webhook signatures')
    # API Key is safer than Auth Token for generating browser tokens
    api_key_sid = models.CharField(max_length=64, blank=True, help_text='API Key SID (SK...) — create in Twilio Console → API Keys')
    api_key_secret = models.CharField(max_length=64, blank=True, help_text='API Key Secret — shown once when created')
    default_from_number = models.CharField(max_length=20, blank=True, help_text='E.164 format e.g. +14155552671')
    twiml_app_sid = models.CharField(max_length=64, blank=True, help_text='TwiML App SID for browser calls')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Twilio — {self.business.name}"

    @property
    def is_configured(self):
        return bool(self.account_sid and self.auth_token and self.default_from_number)

    @property
    def has_api_key(self):
        return bool(self.api_key_sid and self.api_key_secret)


class CallQueue(models.Model):
    STRATEGY_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('simultaneous', 'Simultaneous Ring'),
        ('priority', 'Priority Order'),
    ]
    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE,
        related_name='call_queues'
    )
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, help_text='Twilio number assigned to this queue')
    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES, default='round_robin')
    max_wait_seconds = models.IntegerField(default=120, help_text='Before going to voicemail')
    hold_music_url = models.URLField(blank=True, help_text='MP3 URL for hold music')
    greeting_text = models.TextField(
        default='Thank you for calling. Please hold while we connect you.',
        help_text='Spoken to the caller when they enter the queue'
    )
    voicemail_enabled = models.BooleanField(default=True)
    voicemail_text = models.TextField(
        default='Sorry we missed you. Please leave a message after the tone.',
        blank=True
    )
    agents = models.ManyToManyField(User, blank=True, related_name='call_queues')
    ivr_menu = models.ForeignKey(
        'IVRMenu', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='queues'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    @property
    def available_agents(self):
        return AgentCallStatus.objects.filter(
            business=self.business,
            agent__in=self.agents.all(),
            status='available'
        )

    @property
    def calls_waiting(self):
        return CallLog.objects.filter(queue=self, status='queued').count()


class IVRMenu(models.Model):
    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE,
        related_name='ivr_menus'
    )
    name = models.CharField(max_length=100)
    welcome_message = models.TextField(
        default='Welcome. Press 1 for Sales, Press 2 for Support, Press 0 to speak with an operator.'
    )
    invalid_message = models.TextField(
        default='Sorry, that option is not valid. Please try again.',
        blank=True
    )
    timeout_seconds = models.IntegerField(default=10)
    max_retries = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class IVROption(models.Model):
    ACTION_CHOICES = [
        ('queue', 'Route to Queue'),
        ('message', 'Play Message'),
        ('transfer', 'Transfer to Number'),
        ('voicemail', 'Go to Voicemail'),
        ('hangup', 'Hang Up'),
        ('submenu', 'Go to Sub-menu'),
    ]
    DIGIT_CHOICES = [(str(i), str(i)) for i in range(10)] + [('*', '*'), ('#', '#')]

    menu = models.ForeignKey(IVRMenu, on_delete=models.CASCADE, related_name='options')
    digit = models.CharField(max_length=2, choices=DIGIT_CHOICES)
    label = models.CharField(max_length=100, help_text='e.g. Sales, Support, Billing')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='queue')
    queue = models.ForeignKey(
        CallQueue, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='ivr_options'
    )
    transfer_number = models.CharField(max_length=20, blank=True, help_text='E.164 for external transfer')
    message_text = models.TextField(blank=True, help_text='Text to speak for message action')
    submenu = models.ForeignKey(
        IVRMenu, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='parent_options'
    )

    class Meta:
        unique_together = ('menu', 'digit')
        ordering = ['digit']

    def __str__(self):
        return f"Press {self.digit} — {self.label}"


class CallLog(models.Model):
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('ringing', 'Ringing'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('no-answer', 'No Answer'),
        ('busy', 'Busy'),
        ('failed', 'Failed'),
        ('voicemail', 'Voicemail'),
        ('abandoned', 'Abandoned'),
    ]

    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE,
        related_name='call_logs'
    )
    queue = models.ForeignKey(
        CallQueue, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='call_logs'
    )
    twilio_call_sid = models.CharField(max_length=64, blank=True, db_index=True)
    caller_number = models.CharField(max_length=30)
    called_number = models.CharField(max_length=30)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='inbound')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    agent = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='handled_calls'
    )
    # CRM link — auto-matched or manually set
    contact = models.ForeignKey(
        'crm.Contact', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='call_logs'
    )
    ivr_path = models.CharField(max_length=100, blank=True, help_text='Digits pressed through IVR e.g. 1>2')
    started_at = models.DateTimeField(default=timezone.now)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    wait_seconds = models.IntegerField(default=0)
    recording_url = models.URLField(blank=True)
    recording_sid = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.direction} {self.caller_number} → {self.called_number} [{self.status}]"

    @property
    def duration_display(self):
        if not self.duration_seconds:
            return '—'
        m, s = divmod(self.duration_seconds, 60)
        return f"{m}m {s}s"

    @property
    def wait_display(self):
        if not self.wait_seconds:
            return '—'
        m, s = divmod(self.wait_seconds, 60)
        return f"{m}m {s}s"

    def save(self, *args, **kwargs):
        if self.answered_at and self.started_at:
            self.wait_seconds = max(0, int((self.answered_at - self.started_at).total_seconds()))
        if self.ended_at and self.answered_at:
            self.duration_seconds = max(0, int((self.ended_at - self.answered_at).total_seconds()))
        super().save(*args, **kwargs)


class AgentCallStatus(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('on_call', 'On Call'),
        ('wrap_up', 'Wrap Up'),
        ('break', 'On Break'),
        ('offline', 'Offline'),
    ]

    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE,
        related_name='agent_call_statuses'
    )
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_statuses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    current_call = models.ForeignKey(
        CallLog, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='active_agent_status'
    )
    last_status_change = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('business', 'agent')

    def __str__(self):
        return f"{self.agent.get_full_name() or self.agent.email} — {self.get_status_display()}"
