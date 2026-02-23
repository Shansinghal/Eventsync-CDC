FROM python:3.11-slim
WORKDIR /app
COPY services/rabbit-listener/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/rabbit-listener/src/ ./src/
CMD ["python", "src/main.py"]
