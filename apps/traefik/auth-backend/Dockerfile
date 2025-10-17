FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY auth.py .
COPY dictionary /app/dictionary

EXPOSE 5000

CMD ["uvicorn", "auth:app", "--host", "0.0.0.0", "--port", "5000"]
