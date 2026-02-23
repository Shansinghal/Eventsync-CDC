FROM python:3.11-slim
WORKDIR /app
COPY services/cache-invalidator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/cache-invalidator/src/ ./src/
CMD ["python", "src/main.py"]
