import asyncio
import json
import aio_pika
from celery.exceptions import TimeoutError as CeleryTimeoutError

from app.core.config import RABBITMQ_URL
from app.tasks import process_order_task


async def process_order(message: aio_pika.IncomingMessage):
    try:
        body = json.loads(message.body.decode())
        order_id = body.get('order_id')       
        if order_id:
            task = process_order_task.delay(order_id)
            await asyncio.to_thread(task.get, timeout=60)
            await message.ack()
        else:
            await message.nack(requeue=True)
    except (CeleryTimeoutError, TimeoutError, Exception):
        await message.nack(requeue=True)


async def consume_messages():
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)        
            queue = await channel.declare_queue("new_order", durable=True)
            await queue.consume(process_order)
            try:
                await asyncio.Future()
            except KeyboardInterrupt:
                pass
    except Exception:
        await asyncio.sleep(5)


async def main():
    while True:
        try:
            await consume_messages()
        except Exception:
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())