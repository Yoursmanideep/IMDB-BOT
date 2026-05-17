FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    libxss1 \
    libxtst6 \
    libxrandr2 \
    libxdamage1 \
    libxcomposite1 \
    libxfixes3 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libcups2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for Playwright
RUN python -m playwright install chromium

COPY . .

CMD ["python", "app.py"]
