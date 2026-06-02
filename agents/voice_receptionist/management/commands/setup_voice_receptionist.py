"""
Management command to create or update the BusinessProfile for the Voice Receptionist agent.

Usage:
    python manage.py setup_voice_receptionist
    python manage.py setup_voice_receptionist --slug bengalbound --phone +18664030430
    python manage.py setup_voice_receptionist --slug bengalbound --forwarding +12125550100
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


DEFAULT_HOURS = {
    day: {"open": "09:00", "close": "17:00"}
    for day in ("monday", "tuesday", "wednesday", "thursday", "friday")
}


class Command(BaseCommand):
    help = "Create or update the Voice Receptionist BusinessProfile for a business."

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug', default='bengalbound',
            help='BusinessInstance slug to link to (default: bengalbound)',
        )
        parser.add_argument(
            '--phone',
            default=getattr(settings, 'TWILIO_PHONE_NUMBER', ''),
            help='Twilio phone number to assign (defaults to TWILIO_PHONE_NUMBER env var)',
        )
        parser.add_argument(
            '--forwarding', default='',
            help='Forwarding number for call transfers (optional)',
        )
        parser.add_argument(
            '--agent-name', default='Aria',
            help='AI receptionist display name (default: Aria)',
        )

    def handle(self, *args, **options):
        from hub.models import BusinessInstance
        from agents.voice_receptionist.models import BusinessProfile

        slug = options['slug']
        twilio_number = options['phone']
        forwarding = options['forwarding']
        agent_name = options['agent_name']

        try:
            biz = BusinessInstance.objects.get(slug=slug)
        except BusinessInstance.DoesNotExist:
            raise CommandError(
                f"BusinessInstance with slug '{slug}' not found. "
                f"Available: {list(BusinessInstance.objects.values_list('slug', flat=True))}"
            )

        if not twilio_number:
            raise CommandError(
                "No Twilio phone number provided. Set TWILIO_PHONE_NUMBER in .env "
                "or pass --phone +1XXXXXXXXXX"
            )

        # Use slug as firebase_uid so it's unique and human-readable
        firebase_uid = f"django-{biz.slug}"

        profile, created = BusinessProfile.objects.update_or_create(
            firebase_uid=firebase_uid,
            defaults={
                'business_name':       biz.name,
                'business_type':       'general',
                'phone':               biz.business_phone or twilio_number,
                'twilio_phone_number': twilio_number,
                'forwarding_number':   forwarding,
                'agent_name':          agent_name,
                'business_hours':      DEFAULT_HOURS,
                'services_offered':    ['General Inquiry', 'Appointment Booking', 'Support'],
                'is_active':           True,
            },
        )

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} BusinessProfile for '{biz.name}'\n"
            f"  firebase_uid:        {profile.firebase_uid}\n"
            f"  Twilio number:       {profile.twilio_phone_number}\n"
            f"  Forwarding number:   {profile.forwarding_number or '(none)'}\n"
            f"  Agent name:          {profile.agent_name}\n"
            f"  Business hours:      Mon–Fri 09:00–17:00\n"
        ))

        base = getattr(settings, 'SITE_URL', 'https://yourdomain.com')
        self.stdout.write(self.style.WARNING(
            "\nPaste these URLs into the Twilio Console for " + twilio_number + ":\n"
            f"  Voice webhook (Inbound):  {base}/agents/voice-receptionist/webhook/inbound/\n"
            f"  Status callback:          {base}/agents/voice-receptionist/webhook/transfer-complete/\n"
        ))
