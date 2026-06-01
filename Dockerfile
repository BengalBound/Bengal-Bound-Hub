FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=bengalbound_core.settings.render

WORKDIR /app

# System deps — gcc + libpq needed for psycopg2 compilation
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

EXPOSE 8080

# At startup: collect static → migrate → start gunicorn
# /tmp/staticfiles is always writable in Cloud Run containers
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 bengalbound_core.wsgi:application"]
