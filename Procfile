web: gunicorn bengalbound_core.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py collectstatic --noinput && python manage.py migrate --noinput && python seed_marketing.py
