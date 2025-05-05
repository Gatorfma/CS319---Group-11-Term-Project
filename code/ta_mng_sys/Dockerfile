# ── Dockerfile ──
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for mysqlclient, netcat (for waiting on DB), etc.
RUN apt-get update && \
    apt-get install -y \
      build-essential \
      default-libmysqlclient-dev \
      pkg-config \
      netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# install Python deps
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy your entire project (including src/, docker-compose.yml, Makefile…)
COPY . /app/

# ← no CMD here. docker-compose.yml will supply the start command.
