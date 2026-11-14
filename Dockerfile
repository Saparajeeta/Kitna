# Kitna HTTP service: POST /parse, POST /tool-call/check, GET /health, OpenAPI page at /docs.
#
#   docker build -t kitna .
#   docker run --rm -p 8000:8000 kitna
#   curl -s localhost:8000/parse -H 'content-type: application/json' \
#        -d '{"text": "dhai lakh rupaye", "relative_base": "2026-11-12T10:00"}'
#
# Pre-alpha: the rules are AI-drafted and not validated by native speakers. No rate limiting and no
# authentication are built in; put it behind your own gateway before exposing it to a network.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install ".[serve]" && useradd --create-home --uid 10001 kitna
USER kitna
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health')"
CMD ["kitna", "serve", "--host", "0.0.0.0", "--port", "8000"]
