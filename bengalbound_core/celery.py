"""
bengalbound_core/celery.py
──────────────────────────
Celery application entry point for BengalBound.

Start the worker:   celery -A bengalbound_core worker -l info
Start the beat:     celery -A bengalbound_core beat   -l info
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings')

app = Celery('bengalbound_core')

# Read configuration from Django settings (keys prefixed with CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
