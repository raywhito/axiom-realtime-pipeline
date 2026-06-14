# Producer / consumer image (build context = repo root).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY python/ /app/

# The command (producer.py / consumer.py) is set per service in docker-compose.
CMD ["python", "consumer.py"]
