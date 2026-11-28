FROM python:3.12-slim
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-arphic-uming \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/api services/api
COPY services/ingestion services/ingestion
COPY services/retrieval services/retrieval
COPY alembic.ini .
COPY database/migrations database/migrations
CMD ["python", "-m", "uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
