FROM mcr.microsoft.com/playwright/python:v1.65.1-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    VIEWPORT_WIDTH=1920 \
    VIEWPORT_HEIGHT=1080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/
COPY pytest.ini .

RUN mkdir -p /app/artifacts

CMD ["pytest", "-v", "--tb=short"]
