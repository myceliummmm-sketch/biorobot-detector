FROM python:3.11-slim

# Install ffmpeg for voice message processing
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY prisma_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY prisma_bot/ .

# Run bot
CMD ["python", "bot.py"]
