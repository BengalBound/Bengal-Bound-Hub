"""
python manage.py export_static --settings=netlify_settings

Renders every public-site URL via Django's test client and writes the HTML
to netlify_dist/<path>/index.html.  Static assets are collected separately
by `collectstatic` (also into netlify_dist/static/).
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import Client


PAGES = [
    ('/',             'index.html'),
    ('/about/',       'about/index.html'),
    ('/services/',    'services/index.html'),
    ('/pricing/',     'pricing/index.html'),
    ('/contact/',     'contact/index.html'),
    ('/consult/',     'consult/index.html'),
    ('/hire-ai/',     'hire-ai/index.html'),
    ('/affiliates/',  'affiliates/index.html'),
    ('/trial/',       'trial/index.html'),
    ('/why-us/',      'why-us/index.html'),
    ('/docs/',        'docs/index.html'),
    ('/blog/',        'blog/index.html'),
]


class Command(BaseCommand):
    help = 'Export public site to static HTML for Netlify deployment'

    def handle(self, *args, **options):
        output_dir = Path(settings.BASE_DIR) / 'netlify_dist'

        # Clear previous build output (keep the static/ sub-dir if collectstatic ran first)
        static_backup = output_dir / 'static'
        had_static = static_backup.exists()
        if had_static:
            tmp = Path(settings.BASE_DIR) / '_static_backup'
            shutil.copytree(static_backup, tmp, dirs_exist_ok=True)

        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir()

        if had_static:
            shutil.copytree(Path(settings.BASE_DIR) / '_static_backup', static_backup, dirs_exist_ok=True)
            shutil.rmtree(Path(settings.BASE_DIR) / '_static_backup')

        client = Client()
        success = 0

        for url, rel_path in PAGES:
            try:
                response = client.get(url, HTTP_HOST='localhost')
                if response.status_code == 200:
                    dest = output_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(response.content)
                    self.stdout.write(f'  OK  {url}')
                    success += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  {response.status_code}  {url} — skipped')
                    )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'  ERR {url} — {exc}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nExported {success}/{len(PAGES)} pages -> netlify_dist/'
            )
        )
