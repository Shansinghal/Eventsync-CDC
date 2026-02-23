import os
import time
import json
import logging
import redis
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cache_invalidator")

logger.info("Starting Cache Invalidator Service...")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"), 
    port=int(os.getenv("REDIS_PORT", 6379))
)

# Kafka Consumer connection with retries
bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
topic = os.getenv("KAFKA_TOPIC", "cdc.public.users")
group_id = os.getenv("KAFKA_GROUP_ID", "cache-invalidator")

consumer = None
max_retries = 12
for i in range(max_retries):
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )
        logger.info("Successfully connected to Kafka.")
        break
    except NoBrokersAvailable:
        logger.warning(f"Kafka broker not available. Retrying in 5 seconds... ({i+1}/{max_retries})")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Error connecting to Kafka: {e}")
        time.sleep(5)

if not consumer:
    logger.error("Failed to connect to Kafka after maximum retries. Exiting.")
    exit(1)

logger.info(f"Listening for CDC events on topic: {topic}")

for message in consumer:
    event = message.value
    logger.debug(f"CDC EVENT RECEIVED: {event}")
    
    payload = event.get("payload")
    if payload and payload.get("op") in ["c", "u", "d"]:
        logger.info("Database change detected. Invalidating Redis cache...")
        try:
            redis_client.delete("users_list")
            logger.info("Cache cleared ✅")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")