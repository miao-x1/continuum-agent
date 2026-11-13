FROM node:20-bookworm-slim AS frontend
WORKDIR /build/desktop
COPY desktop/package.json desktop/package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY desktop/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONTINUUM_HOST=0.0.0.0 \
    CONTINUUM_PORT=8765 \
    CONTINUUM_DATA_DIR=/var/lib/continuum/data \
    CONTINUUM_WORKSPACE_DIR=/var/lib/continuum/workspace \
    CONTINUUM_USER_SKILLS_DIR=/var/lib/continuum/skills \
    CONTINUUM_WEB_DIR=/app/web

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && useradd --system --uid 10001 --create-home continuum \
    && mkdir -p /var/lib/continuum/data /var/lib/continuum/workspace /var/lib/continuum/skills \
    && chown -R continuum:continuum /var/lib/continuum
COPY backend/continuum ./continuum
COPY --from=frontend /build/desktop/dist /app/web
USER continuum
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=2)" || exit 1
CMD ["python", "-m", "continuum.server"]
