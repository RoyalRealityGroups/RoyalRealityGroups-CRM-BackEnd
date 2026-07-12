ARG PYTHON_VERSION=3.10.12
FROM python:${PYTHON_VERSION}-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app

RUN python -m venv venv \
&& /app/venv/bin/pip install --upgrade pip \
&& /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV VIRTUAL_ENV=/app/venv
ENV PATH=/app/venv/bin:$PATH

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["/bin/sh","/app/entrypoint.sh"]