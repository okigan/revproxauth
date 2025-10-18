# check=skip=SecretsUsedInArgOrEnv
# Build stage
FROM python:3.12-alpine AS builder

WORKDIR /app

# Set UV to use copy mode to avoid hardlink warnings in Docker
ENV UV_LINK_MODE=copy

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv - exclude dev dependencies
RUN uv sync --frozen --no-dev && \
    # Remove unnecessary files to reduce image size
    find /app/.venv -type d -name "tests" -o -name "test" | xargs rm -rf && \
    find /app/.venv -type f -name "*.pyc" -delete && \
    find /app/.venv -type d -name "__pycache__" -delete && \
    find /app/.venv -name "*.dist-info" -type d -exec sh -c 'rm -f "$1"/{RECORD,INSTALLER,direct_url.json}' _ {} \;

# Runtime stage
FROM python:3.12-alpine

# Metadata labels for container discovery
LABEL org.opencontainers.image.title="RevProxAuth"
LABEL org.opencontainers.image.description="Centralized authentication proxy for Synology NAS with RADIUS support"
LABEL org.opencontainers.image.authors="Igor Okulist <okigan@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/okigan/revproxauth"
LABEL org.opencontainers.image.documentation="https://github.com/okigan/revproxauth#readme"

# Environment variable documentation
LABEL revproxauth.env.RADIUS_SERVER="IP address of RADIUS server (required)"
LABEL revproxauth.env.RADIUS_SECRET="RADIUS shared secret (required)"
LABEL revproxauth.env.RADIUS_PORT="RADIUS server port (default: 1812)"
LABEL revproxauth.env.RADIUS_NAS_IDENTIFIER="NAS identifier (default: revproxauth)"
LABEL revproxauth.env.LOGIN_DOMAIN="Domain for login redirects (required)"
LABEL revproxauth.env.REVPROXAUTH_ADMIN_USERS="Comma-separated admin usernames (optional)"
LABEL revproxauth.env.LOG_LEVEL="Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)"

# Set default environment variables (users MUST override RADIUS_SERVER, RADIUS_SECRET, and LOGIN_DOMAIN)
# Empty values for required/sensitive variables will be visible in Synology UI for users to fill in
ENV RADIUS_SERVER="" \
    RADIUS_SECRET="" \
    RADIUS_PORT="1812" \
    RADIUS_NAS_IDENTIFIER="revproxauth" \
    LOGIN_DOMAIN="" \
    REVPROXAUTH_ADMIN_USERS="" \
    LOG_LEVEL="INFO" \
    NO_COLOR="1" \
    PYTHONUNBUFFERED="1" \
    VIRTUAL_ENV="/app/.venv" \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/.venv/lib/python3.12/site-packages"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code and templates
COPY main.py dictionary ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY config/ ./config/

# Capture Git commit hash as build arg and store in file
ARG GIT_COMMIT=unknown
RUN echo "${GIT_COMMIT}" > /app/git_commit.txt && \
    mkdir -p /app/config && \
    if [ ! -f /app/config/revproxauth.json ]; then \
        echo '{"version":"1.0","mappings":[]}' > /app/config/revproxauth.json; \
    fi

# Expose port
EXPOSE 9000

# Optimize Python for lower memory usage
ENV PYTHONOPTIMIZE=2 \
    PYTHONDONTWRITEBYTECODE=1

# Run uvicorn with optimized settings for lower memory usage
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "9000", \
     "--workers", "1", \
     "--limit-concurrency", "100", \
     "--backlog", "50", \
     "--timeout-keep-alive", "5"]
