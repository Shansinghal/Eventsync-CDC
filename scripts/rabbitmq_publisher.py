import pika
import os

connection = pika.BlockingConnection(
    pika.ConnectionParameters(os.getenv("RABBITMQ_HOST", "localhost"))
)

channel = connection.channel()

# fanout exchange = broadcast
exchange_name = os.getenv("RABBITMQ_EXCHANGE", "cache_purge")
channel.exchange_declare(exchange=exchange_name, exchange_type="fanout")

message = "PURGE_CACHE"

channel.basic_publish(
    exchange="cache_purge",
    routing_key="",
    body=message
)

print("Broadcasted cache purge command")

connection.close()