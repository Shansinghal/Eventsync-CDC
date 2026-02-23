FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    kafka-python \
    redis \
    pika \
    psycopg2-binary

CMD ["bash"]