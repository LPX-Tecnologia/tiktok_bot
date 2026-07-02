FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install moviepy Pillow apscheduler

COPY tiktok_bot.py .
RUN mkdir -p output

CMD ["python", "tiktok_bot.py"]