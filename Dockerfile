# check=skip=SecretsUsedInArgOrEnv
FROM python:3.12-slim

# Metadata labels for container discovery
LABEL org.opencontainers.image.title="SynAuthProxy"
LABEL org.opencontainers.image.description="Centralized authentication proxy for Synology NAS with RADIUS support"
LABEL org.opencontainers.image.authors="Igor Okulist <okigan@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/okigan/synauthproxy"
LABEL org.opencontainers.image.documentation="https://github.com/okigan/synauthproxy#readme"

# Environment variable documentation
LABEL synauthproxy.env.RADIUS_SERVER="IP address of RADIUS server (required)"
LABEL synauthproxy.env.RADIUS_SECRET="RADIUS shared secret (required)"
LABEL synauthproxy.env.RADIUS_PORT="RADIUS server port (default: 1812)"
LABEL synauthproxy.env.RADIUS_NAS_IDENTIFIER="NAS identifier (default: synauthproxy)"
LABEL synauthproxy.env.LOGIN_DOMAIN="Domain for login redirects (required)"
LABEL synauthproxy.env.SYNAUTHPROXY_ADMIN_USERS="Comma-separated admin usernames (optional)"

# Set default environment variables (users MUST override RADIUS_SERVER, RADIUS_SECRET, and LOGIN_DOMAIN)
# Empty values for required/sensitive variables will be visible in Synology UI for users to fill in
ENV RADIUS_SERVER="" \
    RADIUS_SECRET="" \
    RADIUS_PORT="1812" \
    RADIUS_NAS_IDENTIFIER="synauthproxy" \
    LOGIN_DOMAIN="" \
    SYNAUTHPROXY_ADMIN_USERS=""

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and uv.lock
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen

# Copy application code and templates
COPY main.py dictionary ./
COPY templates/ ./templates/
COPY config/ ./config/

# Capture Git commit hash as build arg and store in file
ARG GIT_COMMIT=unknown
RUN echo "${GIT_COMMIT}" > /app/git_commit.txt

# Create config directory and initialize with empty config if needed
RUN mkdir -p /app/config && \
    if [ ! -f /app/config/synauthproxy.json ]; then \
        echo '{"version":"1.0","mappings":[]}' > /app/config/synauthproxy.json; \
    fi

# Expose port
EXPOSE 9000

# Run FastAPI with uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
