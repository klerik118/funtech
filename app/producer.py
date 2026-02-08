import aio_pika
import json

from app.core.config import RABBITMQ_URL


async def publish_new_order(order_id: str):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue('new_order', durable=True)
        
        message = aio_pika.Message(body=json.dumps({'order_id': order_id}).encode())
        await channel.default_exchange.publish(message, routing_key='new_order')