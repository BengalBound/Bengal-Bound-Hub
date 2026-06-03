import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from inspector.models import ComplianceRule


class Command(BaseCommand):
    help = 'Seed the database with initial compliance rules (idempotent — skips existing rule names).'

    def handle(self, *args, **options):
        today = timezone.now().date()
        one_year_later = today + datetime.timedelta(days=365)

        rules = [
            # ── GDPR ──────────────────────────────────────────────────────────────────
            dict(
                name='Lawful Basis Required',
                category='privacy',
                standard_ref='GDPR Art. 6',
                jurisdiction='EU',
                applies_to_agents=['all'],
                rule_description='Personal data must not be processed without a documented lawful basis (consent, contract, legal obligation, vital interest, public task, or legitimate interest).',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='Data Minimisation',
                category='privacy',
                standard_ref='GDPR Art. 5(1)(c)',
                jurisdiction='EU',
                applies_to_agents=['all'],
                rule_description='Only personal data that is adequate, relevant, and limited to what is necessary for the stated purpose may be collected or stored.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='Right to Erasure',
                category='privacy',
                standard_ref='GDPR Art. 17',
                jurisdiction='EU',
                applies_to_agents=['all'],
                rule_description='Systems must be able to delete all personal data for an individual upon request; storing data after an erasure request is prohibited.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='Cross-Border Transfer Restriction',
                category='privacy',
                standard_ref='GDPR Art. 44-49',
                jurisdiction='EU',
                applies_to_agents=['all'],
                rule_description='Personal data must not be transferred outside the EEA unless the destination country has adequate protection or SCCs are in place.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            # ── HIPAA ─────────────────────────────────────────────────────────────────
            dict(
                name='PHI Minimum Necessary',
                category='privacy',
                standard_ref='HIPAA Privacy Rule 45 CFR 164.502(b)',
                jurisdiction='US',
                applies_to_agents=['all'],
                rule_description='Protected Health Information (PHI) must only be disclosed to the minimum extent necessary to accomplish the intended purpose.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='PHI Encryption Required',
                category='cybersecurity',
                standard_ref='HIPAA Security Rule 45 CFR 164.312(a)(2)(iv)',
                jurisdiction='US',
                applies_to_agents=['all'],
                rule_description='Electronic PHI (ePHI) must be encrypted at rest and in transit; unencrypted ePHI in request payloads is a violation.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='Business Associate Agreement',
                category='legal',
                standard_ref='HIPAA 45 CFR 164.502(e)',
                jurisdiction='US',
                applies_to_agents=['all'],
                rule_description='PHI must not be shared with any third-party service that does not have a signed Business Associate Agreement (BAA) on file.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            # ── EU AI Act ─────────────────────────────────────────────────────────────
            dict(
                name='Prohibited AI Practices',
                category='ai_ethics',
                standard_ref='EU AI Act Art. 5',
                jurisdiction='EU',
                applies_to_agents=['all'],
                rule_description='AI systems must not use subliminal manipulation, exploit vulnerabilities of specific groups, conduct social scoring by public authorities, or perform real-time remote biometric identification in public spaces.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='High-Risk AI Transparency',
                category='ai_ethics',
                standard_ref='EU AI Act Art. 13',
                jurisdiction='EU',
                applies_to_agents=['all'],
                rule_description='High-risk AI systems (hiring, credit, healthcare, law enforcement) must provide explanations for automated decisions and allow human oversight.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='AI Output Disclosure',
                category='ai_ethics',
                standard_ref='EU AI Act Art. 52',
                jurisdiction='EU',
                applies_to_agents=['all'],
                rule_description='Users must be informed when they are interacting with an AI system; AI-generated content must be labelled as such.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            # ── PDPA (Singapore) ──────────────────────────────────────────────────────
            dict(
                name='Consent for Collection',
                category='privacy',
                standard_ref='PDPA Part IV',
                jurisdiction='SG',
                applies_to_agents=['all'],
                rule_description="Personal data of Singapore residents must not be collected, used, or disclosed without the individual's explicit consent.",
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            # ── LGPD (Brazil) ─────────────────────────────────────────────────────────
            dict(
                name='Lawful Basis for Processing',
                category='privacy',
                standard_ref='LGPD Art. 7',
                jurisdiction='BR',
                applies_to_agents=['all'],
                rule_description='Personal data of Brazilian residents must only be processed under one of the ten legal bases defined in the LGPD; processing without a legal basis is prohibited.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            # ── Global / Platform-wide ────────────────────────────────────────────────
            dict(
                name='No Plaintext Secrets in Payloads',
                category='cybersecurity',
                standard_ref='OWASP Top 10 A02:2021',
                jurisdiction='Global',
                applies_to_agents=['all'],
                rule_description='API request payloads must not contain plaintext passwords, API keys, secret tokens, or cryptographic private keys.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='Agent Action Scope Limit',
                category='scope',
                standard_ref='NIST AI RMF Map 1.1',
                jurisdiction='Global',
                applies_to_agents=['all'],
                rule_description="An AI agent must not perform actions outside the scope explicitly granted by the organization's subscription; cross-organization data access is prohibited.",
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
            dict(
                name='Rate Limit Compliance',
                category='cybersecurity',
                standard_ref='NIST SP 800-53 SC-5',
                jurisdiction='Global',
                applies_to_agents=['all'],
                rule_description='API consumers must not exceed the rate limits defined for their subscription tier; burst requests designed to circumvent limits are prohibited.',
                is_active=True,
                effective_date=today,
                review_date=one_year_later,
            ),
        ]

        created_count = 0
        skipped_count = 0

        for r_data in rules:
            _, created = ComplianceRule.objects.get_or_create(
                name=r_data['name'],
                standard_ref=r_data['standard_ref'],
                defaults=r_data
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded compliance rules: {created_count} created, {skipped_count} skipped.")
        )
