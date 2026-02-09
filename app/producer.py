"""Продюсер сообщений для RabbitMQ.

Этот модуль отвечает за публикацию сообщений в message queue.
"""

import aio_pika
import json

from app.core.config import RABBITMQ_URL


async def publish_new_order(order_id: str):
    """Пропубликовать сообщение о новом заказе в queue.
    
    Args:
        order_id: ID нового заказа
        
    Note:
        - Проверяет queue 'new_order' с дольностью (durable=True)
        - Отправляет сообщение как JSON
    """
    # Подключаемся к RabbitMQ
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        # Убедваемся queue existe (в настоящем queue persistent)
        await channel.declare_queue('new_order', durable=True)
        
        # Отправляем сообщение в queue
        message = aio_pika.Message(body=json.dumps({'order_id': order_id}).encode())
        await channel.default_exchange.publish(message, routing_key='new_order')