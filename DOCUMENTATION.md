# Документация Order Management System

## Обзор архитектуры

Это асинхронное приложение FastAPI для управления заказами с использованием микросервисной архитектуры. Система включает обработку очередей, кеширование, аутентификацию и ограничение скорости запросов.

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│              (run.py / app/routers)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    PostgreSQL      Redis         RabbitMQ
    (Data Store)   (Cache &       (Message
                   Rate Limit)    Queue)
                       │              │
                       └──────┬───────┘
                              │
                    ┌─────────▼─────────┐
                    │   Consumer &      │
                    │  Celery Worker    │
                    │   (consumer.py)   │
                    └───────────────────┘
```

## Компоненты системы

### 1. FastAPI Приложение (`run.py`)

**Назначение**: Основной REST API сервер.

**Ключевые компоненты**:
- Health check endpoint (`GET /health`)
- CORS middleware для кроссдоменных запросов
- JWT middleware для проверки токенов
- Rate limiting с использованием Redis

**Маршруты**:
- `/register` - регистрация пользователя
- `/token` - получение JWT токена
- `/orders/` - создание заказа
- `/orders/{order_id}/` - получение заказа
- `/orders/user/{user_id}` - получение всех заказов пользователя

### 2. Аутентификация (`app/security.py`)

**Функции**:
- **`check_token()`** - проверка и декодирование JWT токенов
- **`get_id_current_user()`** - получение ID авторизованного пользователя
- **`hash_password()`** - хеширование пароля с использованием argon2
- **`verify_password()`** - проверка пароля
- **`get_user_or_ip_key()`** - определение ключа для rate limiting

**Алгоритм**: RSA 256-bit (RS256)
**Время жизни токена**: 60 минут

### 3. Маршруты

#### Auth Router (`app/routers/auth.py`)
- `POST /register/` - регистрация с валидацией email
- `POST /token` - логин с получением JWT токена

#### Order Router (`app/routers/order.py`)
- `POST /orders/` - создание заказа (5 рек/мин)
- `GET /orders/{order_id}/` - получение заказа с кешированием (10 рек/мин)
- `PATCH /orders/{order_id}/` - обновление статуса (5 рек/мин)
- `GET /orders/user/{user_id}` - получение всех заказов (10 рек/мин)

### 4. Репозитории

#### OrdersRepository (`app/repositories/orders.py`)
- `create_order()` - создание нового заказа
- `get_order_by_id()` - получение заказа по ID
- `get_orders_by_user_id()` - получение всех заказов пользователя
- `update_order()` - обновление статуса заказа

#### UserRepository (`app/repositories/user.py`)
- `check_for_user_existence()` - проверка существования пользователя
- `adding_user()` - добавление нового пользователя
- `get_user_by_email()` - получение пользователя по email
- `checking_user_id()` - проверка существования пользователя по ID

### 5. Модели БД (`app/database/model.py`)

#### User
```python
- id: Integer (PK, autoincrement)
- email: String (unique, not null)
- hashed_password: String (not null)
- orders: Relationship with Order
```

#### Order
```python
- id: UUID (PK, default=uuid.uuid4)
- user_id: Integer (FK to users.id, cascade delete)
- items: JSON (product data)
- total_price: Decimal (10,2)
- status: Enum (PENDING, PAID, SHIPPED, CANCELED)
- created_at: DateTime (UTC, default=now)
```

#### OrderStatus Enum
- `PENDING` - Заказ создан, ожидает обработки
- `PAID` - Заказ оплачен
- `SHIPPED` - Заказ отправлен
- `CANCELED` - Заказ отменен

### 6. Асинхронная обработка

#### Producer (`app/producer.py`)
Отправляет сообщения в RabbitMQ очередь `new_order` при создании заказа.

```python
async def publish_new_order(order_id: str)
```

#### Consumer (`consumer.py`)
Слушает сообщения из RabbitMQ и отправляет их в Celery для обработки.

```python
async def process_order(message)  # Обработчик сообщений
async def consume_messages()      # Основной лооп консумера
```

#### Celery Tasks (`app/tasks.py`)
```python
@celery_app.task(bind=True, max_retries=3)
def process_order_task(self, order_id: str)
```

**Параметры**:
- `bind=True` - передача контекста задачи
- `max_retries=3` - максимум 3 повторные попытки
- Время ожидания перед повтором: 60 секунд

### 7. Кеширование (`app/database/database.py`)

**Redis использование**:
- **Order Cache**: `order:{order_id}` - кеш заказа (300 сек)
- **Rate Limit**: отдельное Redis для отслеживания лимитов
- **Celery Results**: результаты асинхронных задач

## Поток обработки заказа

```
1. POST /orders/
   ↓
2. Проверка JWT токена
   ↓
3. Валидация данных заказа
   ↓
4. Сохранение в PostgreSQL
   ↓
5. Публикация сообщения в RabbitMQ (producer)
   ↓
6. Return order_id пользователю
   
ФОНОВО:
7. Consumer слушает очередь
   ↓
8. При получении отправляет Celery task
   ↓
9. Celery worker обрабатывает задачу
   ↓
10. Результат сохраняется в Redis
```

## Валидация данных

### UserRegister
- `email` - валидный email адрес
- `password` - 5-20 символов, только буквы и цифры

### OrderCreate
- `items` - список словарей с именами товаров и количеством (>= 1)
- `total_price` - положительная сумма (макс 10 цифр, 2 знака после запятой)

### OrderUpdate
- `status` - один из статусов: PENDING, PAID, SHIPPED, CANCELLED

## Rate Limiting (замедление)

Использует токены Redis для отслеживания лимитов:

- **Создание заказа**: 5 запросов в минуту
- **Получение заказа**: 10 запросов в минуту
- **Обновление заказа**: 5 запросов в минуту
- **Получение заказов пользователя**: 10 запросов в минуту

Лимиты различаются для авторизованных пользователей и анонимных по IP.

## Конфигурация окружения

Требуемые переменные в `.env`:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=order_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

REDIS_URL=redis://localhost:6379/0
REDIS_URL_RATE_LIMIT=redis://localhost:6379/1
REDIS_URL_CELERY=redis://localhost:6379/2

RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

## Обработка ошибок

### HTTP Status Codes
- `200` - OK
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized (токен истек или неверен)
- `404` - Not Found
- `429` - Too Many Requests (rate limit)
- `500` - Internal Server Error

### Исключения
- `HTTPException` - основное исключение API
- `jwt.ExpiredSignatureError` - токен истек
- `jwt.InvalidTokenError` - токен невалиден
- `CeleryTimeoutError` - таслия Celery превышила timeout

## Безопасность

1. **JWT Аутентификация**
   - RSA 256-bit подпись
   - Проверка подписи на каждый запрос
   - Проверка истечения токена

2. **Хеширование паролей**
   - Алгоритм: argon2
   - Автоматическое хеширование при регистрации

3. **Rate Limiting**
   - Защита от bruteforce атак
   - Различные лимиты для разных операций

4. **Middleware Security**
   - CORS ограничения
   - Обработка исключений
   - Логирование JWT попыток

## Развертывание

### Зависимости
```
fastapi
uvicorn
sqlalchemy
asyncpg
redis
aio-pika
celery
passlib[argon2]
pydantic[email]
slowapi
python-dotenv
```

### Запуск приложения
```bash
uvicorn run:app --host 0.0.0.0 --port 8000
```

### Запуск Celery worker
```bash
celery -A app.celery_app worker --loglevel=info
```

### Запуск consumer
```bash
python consumer.py
```

