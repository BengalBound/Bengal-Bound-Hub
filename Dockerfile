FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production

WORKDIR /app

# System deps — gcc + libpq needed for psycopg2 compilation
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Collect static files at build time (whitenoise serves them)
# SECRET_KEY default set in production.py so collectstatic works without env vars
RUN mkdir -p staticfiles && python manage.py collectstatic --noinput

EXPOSE 8080

# Run migrations then start gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 bengalbound_core.wsgi:application"]
