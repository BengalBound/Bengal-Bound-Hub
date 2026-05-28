"""
management/commands/update_spam_blocklist.py
--------------------------------------------
Django management command to refresh the community spam blocklist.

Usage:
    python manage.py update_spam_blocklist
    python manage.py update_spam_blocklist --dry-run
    python manage.py update_spam_blocklist --source community

Schedule via cron (weekly) or APScheduler.
"""

import json
import logging
import urllib.request
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

# Free community spam number sources (adjust URLs as available)
BLOCKLIST_SOURCES = {
    "community": "https://raw.githubusercontent.com/sundowndev/phoneinfoga/master/tests/testdata/numbers.json",
    # Add more sources here — any JSON array of phone number strings
}


class Command(BaseCommand):
    help = "Update the spam phone number blocklist from community sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default="community",
            choices=list(BLOCKLIST_SOURCES.keys()),
            help="Source key to fetch numbers from.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print stats without writing to the database.",
        )
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to a local JSON file containing a list of phone numbers.",
        )

    def handle(self, *args, **options):
        from voice_receptionist.models import SpamBlocklist

        source  = options["source"]
        dry_run = options["dry_run"]
        file_path = options.get("file")

        self.stdout.write(self.style.NOTICE(f"Fetching spam blocklist [source={source}, dry_run={dry_run}]..."))

        # Load numbers
        numbers = []
        try:
            if file_path:
                with open(file_path, "r") as f:
                    numbers = json.load(f)
            else:
                url = BLOCKLIST_SOURCES[source]
                with urllib.request.urlopen(url, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    # Handle both flat list and {"numbers": [...]} structure
                    if isinstance(data, list):
                        numbers = data
                    elif isinstance(data, dict):
                        numbers = data.get("numbers", data.get("data", []))
        except Exception as e:
            raise CommandError(f"Failed to fetch blocklist: {e}")

        if not isinstance(numbers, list):
            raise CommandError("Blocklist data must be a JSON array of phone number strings.")

        # Normalize to strings
        numbers = [str(n).strip() for n in numbers if n]
        total   = len(numbers)
        self.stdout.write(f"Found {total} numbers in source.")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run complete. Would insert/update {total} entries."))
            return

        # Bulk upsert
        existing = set(SpamBlocklist.objects.values_list("phone_number", flat=True))
        new_numbers = [n for n in numbers if n not in existing]
        if new_numbers:
            SpamBlocklist.objects.bulk_create(
                [SpamBlocklist(phone_number=n, source=source) for n in new_numbers],
                ignore_conflicts=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Added {len(new_numbers)} new numbers. Skipped {total - len(new_numbers)} existing."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Blocklist already up to date ({total} entries, no new numbers)."))
