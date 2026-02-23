import os
import time
import logging
import pika
import redis

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("rabbit_listener")

logger.info("Starting RabbitMQ Listener Service...")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"), 
    port=int(os.getenv("REDIS_PORT", 6379)), 
    decode_responses=True
)

# RabbitMQ connection with retries
rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
exchange_name = os.getenv("RABBITMQ_EXCHANGE", "cache_purge")

connection = None
max_retries = 12
for i in range(max_retries):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host)
        )
        logger.info("Successfully connected to RabbitMQ.")
        break
    except pika.exceptions.AMQPConnectionError:
        logger.warning(f"RabbitMQ not available. Retrying in 5 seconds... ({i+1}/{max_retries})")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Error connecting to RabbitMQ: {e}")
        time.sleep(5)

if not connection:
    logger.error("Failed to connect to RabbitMQ after maximum retries. Exiting.")
    exit(1)

channel = connection.channel()

# Setup exchange and queue
channel.exchange_declare(exchange=exchange_name, exchange_type="fanout")
result = channel.queue_declare(queue="", exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange=exchange_name, queue=queue_name)

logger.info("Waiting for purge commands...")

def callback(ch, method, properties, body):
    logger.info(f"PURGE COMMAND RECEIVED: {body}")
    try:
        redis_client.delete("users_list")
        logger.info("Cache cleared via RabbitMQ ✅")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")

channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=True
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    logger.info("Stopping RabbitMQ Listener...")
    channel.stop_consuming()
    connection.close()