"""
WSGI config for bengalbound_core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import threading
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings.production')

application = get_wsgi_application()

def run_db_setup():
    # Only run DB setup if K_SERVICE is set (meaning we are running on Cloud Run)
    if 'K_SERVICE' not in os.environ:
        return
        
    lock_file = '/tmp/db_setup.lock'
    try:
        # Try to acquire lock to ensure only one worker runs this
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        # Another worker process is already doing this
        return
    except Exception as e:
        print(f"Could not create DB setup lock file: {e}")
        pass

    try:
        from django.core.management import call_command
        print("Running migrations asynchronously in background thread...")
        call_command('migrate', interactive=False)
        
        import seed_marketing
        print("Seeding marketing database asynchronously...")
        seed_marketing.seed_db()
        print("Async database setup complete!")
    except Exception as e:
        print(f"Error in async database setup: {e}")

# Start the DB setup in a background daemon thread
# This ensures that Gunicorn binds immediately and starts listening on $PORT!
threading.Thread(target=run_db_setup, daemon=True).start()

