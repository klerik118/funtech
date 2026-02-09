# Техническое задание: Сервис управления заказами

## 1. Введение

Разработать сервис управления заказами на FastAPI, поддерживающий аутентификацию,
работу с очередями сообщений, кеширование и фоновую обработку задач.

## 2. Функциональные требования

### 2.1 API эндпоинты

| Метод | URL | Описание |
| --- | --- | --- |
| POST | /register/ | Регистрация пользователя (email, пароль) |
| POST | /token | Получение JWT-токена (OAuth2) |
| POST | /orders/ | Создание заказа (только авторизованные) |
| GET | /orders/{order_id}/ | Получение заказа (сначала из Redis) |
| PATCH | /orders/{order_id}/ | Обновление статуса заказа |
| GET | /orders/user/{user_id}/ | Получение заказов пользователя |

### 2.2 База данных (PostgreSQL)

Таблица orders:

- id (UUID, primary key)
- user_id (int, ForeignKey на пользователей)
- items (JSON, список товаров)
- total_price (Decimal(10, 2), точность до 2 знаков)
- status (enum: PENDING, PAID, SHIPPED, CANCELED)
- created_at (datetime)

### 2.3 Очереди сообщений (RabbitMQ)

- RabbitMQ используется как брокер сообщений между сервисами (event-bus), а не как брокер Celery.
- При создании заказа сервис публикует событие new_order в очередь.
- Отдельный consumer (отдельный сервис) подписывается на очередь,
	получает сообщения new_order, выполняет обработку и запускает фоновую задачу
	в Celery/taskiq.
- Celery/taskiq используется только для выполнения фоновых задач и не читает RabbitMQ напрямую как event-bus.

### 2.4 Redis (Кеширование заказов)

- Если заказ запрашивается повторно, отдавать его из кеша (TTL = 5 минут).
- При изменении заказа обновлять кеш.

### 2.5 Celery/taskiq (Фоновая обработка)

- Фоновая задача обработки заказа (time.sleep(2) и print(f"Order {order_id} processed")).

### 2.6 Безопасность

- JWT-аутентификация (OAuth2 Password Flow).
- CORS-защита (ограничение кросс-доменных запросов).
- Rate limiting (ограничение частоты запросов на API).
- SQL-инъекции: только ORM-запросы.

## 3. Нефункциональные требования

- Использование FastAPI с Pydantic.
- Работа с PostgreSQL через SQLAlchemy + Alembic.
- Асинхронное взаимодействие с RabbitMQ (брокер сообщений).
- Redis для кеширования и rate limiting.
- Docker Compose для развертывания всей инфраструктуры.
- Код должен быть структурированным и документированным.

## Установка и запуск

### Требования

- Docker Desktop
- Docker Compose

### Настройка окружения

1. Создать файл окружения:

```bash
cp .env.example .env
```

2. Отредактировать .env и задать пароли/секреты.

3. Сгенерировать JWT ключи (RSA):

```bash
# Windows PowerShell
mkdir .secret_key
openssl genrsa -out .secret_key/jwt-private.pem 2048
openssl rsa -in .secret_key/jwt-private.pem -pubout -out .secret_key/jwt-public.pem
```

```bash
# Linux/Mac
mkdir -p .secret_key
openssl genrsa -out .secret_key/jwt-private.pem 2048
openssl rsa -in .secret_key/jwt-private.pem -pubout -out .secret_key/jwt-public.pem
```

### Запуск

```bash
docker-compose up --build
```

### Доступные сервисы

- **FastAPI приложение**: http://localhost:8000
- **FastAPI документация (Swagger)**: http://localhost:8000/docs
- **RabbitMQ Management UI**: http://localhost:15672 (guest/guest)
- **PgAdmin**: http://localhost:5050 (если настроен в docker-compose)
- **RedisInsight**: http://localhost:5540 (если настроен в docker-compose)

### Примечания

- Alembic миграции выполняются при старте контейнера приложения.
- Consumer читает сообщения из очереди и передает задачи в Celery.
