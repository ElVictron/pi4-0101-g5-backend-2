FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0

WORKDIR /srv/backend2
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir . && useradd --system --uid 10002 backend2

USER backend2
EXPOSE 8443
CMD ["python", "-m", "app"]
