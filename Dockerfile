FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy pyproject.toml
COPY pyproject.toml ./

# Install dependencies with uv
# RUN uv sync --frozen --no-cache
RUN uv sync

# Copy application code and templates
COPY main.py dictionary templates/ ./
COPY config/ ./config/

# Run FastAPI with uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
