"""
serea/management/commands/serea_live_test.py
─────────────────────────────────────────────
Live end-to-end test for the Serea AI Employee.
Creates a temporary SereaAgent, runs a scripted conversation + moderation
test, then tears everything down.

Usage:
    python manage.py serea_live_test
    python manage.py serea_live_test --model llama3-8b-8192
    python manage.py serea_live_test --model meta-llama/llama-3.1-8b-instruct:free --openrouter-key sk-or-xxx
    python manage.py serea_live_test --keep-data   # don't delete test records
"""

import os
import time
import textwrap

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from workspace_admin.models import AIEmployeeTier, HiredAIEmployee
from serea.models import (
    SereaAgent, AgentInstruction, ConversationMessage,
    ContentQueue, SereaReport, ModerationLog,
)
from serea.logic import SereaBrain, TokenLimitExceeded


# ANSI colours for readable output
GREEN  = '\033[92m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
RED    = '\033[91m'
BOLD   = '\033[1m'
RESET  = '\033[0m'


def _hr(char='─', width=70):
    return char * width


class Command(BaseCommand):
    help = 'Live end-to-end test of the Serea AI Employee (makes real API calls)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            default='llama3-8b-8192',
            help='Model to use (default: llama3-8b-8192). For OpenRouter use "org/model:free".',
        )
        parser.add_argument('--groq-key',    default=None, help='Override GROQ_API_KEY')
        parser.add_argument('--openrouter-key', default=None, help='Override OPENROUTER_API_KEY')
        parser.add_argument(
            '--keep-data', action='store_true',
            help='Do not delete the test agent/user after the run.',
        )

    def handle(self, *args, **options):
        model        = options['model']
        groq_key     = options['groq_key']     or os.getenv('GROQ_API_KEY', '')
        or_key       = options['openrouter_key'] or os.getenv('OPENROUTER_API_KEY', '')
        keep_data    = options['keep_data']

        # Determine which key we need
        is_openrouter = '/' in model
        is_openai     = model in {'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'}

        if is_openrouter and not or_key:
            raise CommandError(
                'OpenRouter model selected but no OPENROUTER_API_KEY found. '
                'Pass --openrouter-key or set the env var.'
            )
        if not is_openrouter and not is_openai and not groq_key:
            raise CommandError(
                'Groq model selected but no GROQ_API_KEY found. '
                'Pass --groq-key or set the env var.'
            )

        self.stdout.write(f"\n{BOLD}{_hr('═')}{RESET}")
        self.stdout.write(f"{BOLD}  Serea Live Test  —  model: {CYAN}{model}{RESET}")
        self.stdout.write(f"{BOLD}{_hr('═')}{RESET}\n")

        # ── Create test fixtures ──────────────────────────────────────────────
        self.stdout.write(f"{YELLOW}[SETUP]{RESET} Creating test fixtures...")

        ts = int(time.time())
        test_email = f'serea_test_{ts}@test.local'
        user = User.objects.create_user(
            username=f'serea_test_{ts}', email=test_email, password='x', role='console_user'
        )

        tier, _ = AIEmployeeTier.objects.get_or_create(
            name='Test Tier',
            defaults={'monthly_price_usd': 0, 'token_limit': 0, 'description': 'Live test tier'},
        )
        hired = HiredAIEmployee.objects.create(
            employer=user, tier=tier, ai_name='Serea Live Test', is_active=True,
        )
        agent = SereaAgent.objects.create(
            tenant=user,
            hired_employee=hired,
            tier='mid',
            ai_model=model,
            groq_api_key=groq_key or None,
            openrouter_api_key=or_key or None,
            token_limit_override=0,   # unlimited for testing
            status='idle',
        )

        self.stdout.write(f"  Agent created: {GREEN}ID #{agent.pk}{RESET} ({model})\n")

        try:
            brain = SereaBrain(agent_id=agent.pk)
            self.stdout.write(f"{GREEN}[OK]{RESET} SereaBrain initialised successfully.\n")
        except Exception as e:
            self._cleanup(user, hired, agent, keep_data)
            raise CommandError(f'SereaBrain init failed: {e}')

        results = []

        # ── Test 1: Basic chat greeting ───────────────────────────────────────
        results.append(self._run_chat(brain, agent, 1,
            "Hey Serea! Just checking in — introduce yourself briefly.",
            expect_keywords=[],
        ))

        # ── Test 2: Natural task — write an Instagram post ────────────────────
        results.append(self._run_chat(brain, agent, 2,
            "Write me a short Instagram post for a summer sale. Use relevant hashtags. Schedule it.",
            expect_keywords=['instagram', 'hashtag', '#', 'schedule', 'post'],
        ))

        # ── Test 3: Check what was scheduled ─────────────────────────────────
        results.append(self._run_chat(brain, agent, 3,
            "What posts do I have scheduled right now?",
            expect_keywords=['scheduled', 'instagram', 'summer'],
        ))

        # ── Test 4: Stats ─────────────────────────────────────────────────────
        results.append(self._run_chat(brain, agent, 4,
            "Give me a quick summary of how things are going this month.",
            expect_keywords=['moderation', 'token', 'stats', 'month'],
        ))

        # ── Test 5: Save a client instruction ────────────────────────────────
        results.append(self._run_chat(brain, agent, 5,
            "From now on, always end your posts with 'Powered by BengalBound ✨'. Remember that.",
            expect_keywords=['saved', 'instruction', 'bengalbound', 'remember'],
        ))

        # ── Test 6: Report generation ─────────────────────────────────────────
        results.append(self._run_chat(brain, agent, 6,
            "Generate a moderation report for this month and save it.",
            expect_keywords=['report', 'moderation', 'saved', 'month'],
        ))

        # ── Test 7: Moderation — obvious spam ────────────────────────────────
        results.append(self._run_moderation(brain, agent, 7,
            comment="CLICK HERE FOR FREE FOLLOWERS!!! LIMITED TIME ONLY!! 🔥🔥",
            platform='Instagram',
            expect_action_in=['delete', 'flag', 'pending_approval'],
        ))

        # ── Test 8: Moderation — positive comment ────────────────────────────
        results.append(self._run_moderation(brain, agent, 8,
            comment="Love your products! Been a customer for 3 years. Keep it up!",
            platform='Facebook',
            expect_action_in=['reply', 'ignore', 'flag'],
        ))

        # ── Test 9: Memory / continuity ───────────────────────────────────────
        results.append(self._run_chat(brain, agent, 9,
            "Do you remember the instruction I gave you earlier about posts?",
            expect_keywords=['bengalbound', 'powered', '✨'],
        ))

        # ── Test 10: Daily briefing ───────────────────────────────────────────
        self.stdout.write(f"\n{_hr()}")
        self.stdout.write(f"{CYAN}[TEST 10]{RESET} Daily Briefing\n")
        try:
            briefing = brain.generate_daily_briefing()
            self.stdout.write(f"  Response: {GREEN}{textwrap.fill(briefing, 70, subsequent_indent='    ')}{RESET}")
            results.append(('Daily Briefing', True, ''))
        except Exception as e:
            self.stdout.write(f"  {RED}FAILED: {e}{RESET}")
            results.append(('Daily Briefing', False, str(e)))

        # ── Summary ──────────────────────────────────────────────────────────
        self._print_summary(results, agent)

        # ── Cleanup ──────────────────────────────────────────────────────────
        self._cleanup(user, hired, agent, keep_data)

    def _run_chat(self, brain, agent, num, message, expect_keywords=None):
        self.stdout.write(f"\n{_hr()}")
        self.stdout.write(f"{CYAN}[TEST {num}]{RESET} {message[:80]}")
        try:
            reply = brain.chat(message)
            wrapped = textwrap.fill(reply, 70, subsequent_indent='    ')
            self.stdout.write(f"  {GREEN}Serea:{RESET} {wrapped}")

            # Check DB side effects
            agent.refresh_from_db()
            self.stdout.write(
                f"  {YELLOW}Tokens this month:{RESET} {agent.tokens_used_this_month:,}"
            )

            # Soft keyword check
            missing = []
            if expect_keywords:
                reply_lower = reply.lower()
                missing = [k for k in expect_keywords if k.lower() not in reply_lower]
                if missing:
                    self.stdout.write(
                        f"  {YELLOW}Note:{RESET} Keywords not found in reply: {missing}"
                    )

            return (f'Chat #{num}', True, '')
        except TokenLimitExceeded as e:
            self.stdout.write(f"  {RED}TOKEN LIMIT: {e}{RESET}")
            return (f'Chat #{num}', False, f'TokenLimitExceeded: {e}')
        except Exception as e:
            self.stdout.write(f"  {RED}ERROR: {e}{RESET}")
            return (f'Chat #{num}', False, str(e))

    def _run_moderation(self, brain, agent, num, comment, platform, expect_action_in):
        self.stdout.write(f"\n{_hr()}")
        self.stdout.write(f"{CYAN}[TEST {num}]{RESET} Moderation ({platform}): {comment[:60]}")
        try:
            result = brain.process_comment(comment, platform=platform)
            action     = result['action']
            confidence = result.get('confidence')
            sentiment  = result.get('sentiment')
            ok         = action in expect_action_in

            status_icon = f"{GREEN}✓{RESET}" if ok else f"{YELLOW}⚠{RESET}"
            self.stdout.write(
                f"  {status_icon} Action: {BOLD}{action}{RESET}  "
                f"| Confidence: {confidence}  | Sentiment: {sentiment}"
            )
            if not ok:
                self.stdout.write(
                    f"  {YELLOW}Note:{RESET} Expected action in {expect_action_in}, got '{action}'"
                )
            return (f'Moderation #{num}', True, '')
        except Exception as e:
            self.stdout.write(f"  {RED}ERROR: {e}{RESET}")
            return (f'Moderation #{num}', False, str(e))

    def _print_summary(self, results, agent):
        self.stdout.write(f"\n{BOLD}{_hr('═')}{RESET}")
        self.stdout.write(f"{BOLD}  TEST SUMMARY{RESET}")
        self.stdout.write(_hr('═'))

        passed = sum(1 for _, ok, _ in results if ok)
        failed = len(results) - passed

        for name, ok, err in results:
            icon = f"{GREEN}✓ PASS{RESET}" if ok else f"{RED}✗ FAIL{RESET}"
            suffix = f"  — {RED}{err}{RESET}" if not ok else ''
            self.stdout.write(f"  {icon}  {name}{suffix}")

        agent.refresh_from_db()

        self.stdout.write(_hr())
        self.stdout.write(
            f"  Results: {GREEN}{passed} passed{RESET} / {RED}{failed} failed{RESET}"
        )
        self.stdout.write(
            f"  Total tokens used: {CYAN}{agent.tokens_used_this_month:,}{RESET}"
        )
        self.stdout.write(
            "  DB records created:"
        )
        self.stdout.write(f"    ConversationMessages : {ConversationMessage.objects.filter(agent=agent).count()}")
        self.stdout.write(f"    ContentQueue items   : {ContentQueue.objects.filter(agent=agent).count()}")
        self.stdout.write(f"    SereaReports         : {SereaReport.objects.filter(agent=agent).count()}")
        self.stdout.write(f"    ModerationLogs       : {ModerationLog.objects.filter(agent=agent).count()}")
        self.stdout.write(f"    AgentInstructions    : {AgentInstruction.objects.filter(agent=agent).count()}")
        self.stdout.write(f"{BOLD}{_hr('═')}{RESET}\n")

    def _cleanup(self, user, hired, agent, keep_data):
        if keep_data:
            self.stdout.write(
                f"{YELLOW}[KEEP]{RESET} Test data kept. Agent ID #{agent.pk}, User: {user.email}"
            )
            return
        self.stdout.write(f"{YELLOW}[CLEANUP]{RESET} Deleting test records...")
        agent.delete()
        hired.delete()
        user.delete()
        self.stdout.write(f"{GREEN}[DONE]{RESET} Test data removed.\n")
