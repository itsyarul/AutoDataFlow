# Dockerfile (paste into repo root)
FROM python:3.11-slim

# ---- system deps for Playwright / headless browsers ----
# (based on Playwright recommendations; keeps image reasonably small)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libx11-6 \
    libxcomposite1 \
    libxrandr2 \
    libxcursor1 \
    libdbus-1-3 \
    libgbm1 \
    fonts-liberation \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    xdg-utils \
    git \
    && rm -rf /var/lib/apt/lists/*

# set working dir
WORKDIR /app

# copy package lists first for Docker cache efficiency
COPY requirements.txt /app/requirements.txt

# install pip deps
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# install Playwright browsers
# NOTE: this downloads browser binaries (chromium) into the image.
RUN python -m playwright install --with-deps chromium

# copy project
COPY . /app

# create data dir for exports
RUN mkdir -p /app/data
RUN chmod +x /app/start.sh

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# default command used by docker-compose (api service may override)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
