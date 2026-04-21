FROM python:3.12-slim

WORKDIR /app

# Системные зависимости (нужны для WeasyPrint и psycopg)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Зависимости Python
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system -e ".[dev]"

COPY . .

EXPOSE 8000
