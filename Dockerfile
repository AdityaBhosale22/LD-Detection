FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Train the baseline model and collect static files (Django admin) at build time,
# so the image is self-contained
RUN python ml/build_baseline.py \
 && DJANGO_DEBUG=0 DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

# Run as a non-root user
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# PORT is injected by hosts like Render (defaults to 8000).
# WEB_CONCURRENCY is read by gunicorn as the number of worker processes.
ENV PORT=8000 \
    WEB_CONCURRENCY=2
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz/' % os.environ['PORT'], timeout=4)"

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
CMD ["sh", "-c", "exec gunicorn lddiag.wsgi:application --bind 0.0.0.0:$PORT --access-logfile -"]
