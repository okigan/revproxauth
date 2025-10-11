FROM python:3.12-slim

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

# Create config directory and initialize with empty config if needed
RUN mkdir -p /app/config && \
    if [ ! -f /app/config/synauthproxy.json ]; then \
        echo '{"version":"1.0","mappings":[]}' > /app/config/synauthproxy.json; \
    fi

# Expose port
EXPOSE 9000

# Run FastAPI with uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
