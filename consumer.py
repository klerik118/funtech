"""Консюмер сообщений для RabbitMQ.

Этот скрипт самоятельные сообщения о новых заказах на эскiid
иотправляет асинхронные таски в Celery для фоновой обработки.
"""

import asyncio
import json
import aio_pika
from celery.exceptions import TimeoutError as CeleryTimeoutError

from app.core.config import RABBITMQ_URL
from app.tasks import process_order_task


async def process_order(message: aio_pika.IncomingMessage):
    """Обработать сообщение о новом заказе.
    
    Args:
        message: Полученное сообщение из RabbitMQ
        
    Note:
        - Пренджосит Celery task для обработки
        - Не делаем message acknowledge (аск) в случае ошибки
    """
    try:
        body = json.loads(message.body.decode())
        order_id = body.get('order_id')       
        if order_id:
            # Направляем таск и ждем результата
            task = process_order_task.delay(order_id)
            await asyncio.to_thread(task.get, timeout=60)
            # Подтверждаем обработку
            await message.ack()
        else:
            # Не аэандзируем и вернем в queue
            await message.nack(requeue=True)
    except (CeleryTimeoutError, TimeoutError, Exception):
        # Ошибка при обработке - вернем в queue
        await message.nack(requeue=True)


async def consume_messages():
    """Консумировать messages из RabbitMQ queue.
    
    Note:
        - Прослушиваем единочине сообщения (префетч=1)
        - Все сообщений queue 'new_order' являются персистентными
    """
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            # тексимум 1 сообщение за раз
            await channel.set_qos(prefetch_count=1)        
            queue = await channel.declare_queue("new_order", durable=True)
            await queue.consume(process_order)
            try:
                # Ждем до покрытия Клавбордпрерывание
                await asyncio.Future()
            except KeyboardInterrupt:
                pass
    except Exception:
        # Ошибка при подключении - рассматриваем форски 5 секунд
        await asyncio.sleep(5)


async def main():
    """Основной лооп для консумера.
    
    Циклически пытается ноподключиться и потребlíать messages.
    """
    while True:
        try:
            await consume_messages()
        except Exception:
            # Пара на 5 секунд лорнов попытки
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())