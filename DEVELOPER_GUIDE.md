# Гайд для разработчиков

## Структура проекта

```
.
├── app/
│   ├── __init__.py
│   ├── celery_app.py          # Конфигурация Celery
│   ├── producer.py            # Отправка сообщений в RabbitMQ
│   ├── schemas.py             # Pydantic модели для валидации
│   ├── security.py            # Аутентификация и безопасность
│   ├── tasks.py               # Асинхронные Celery таски
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Конфигурация приложения
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py        # Подключение БД и Redis
│   │   └── model.py           # SQLAlchemy модели
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── orders.py          # CRUD для заказов
│   │   └── user.py            # CRUD для пользователей
│   └── routers/
│       ├── __init__.py
│       ├── auth.py            # Маршруты регистрации/логина
│       └── order.py           # Маршруты управления заказами
├── alembic/                   # Миграции БД (Alembic)
├── run.py                     # Точка входа приложения
├── consumer.py                # Consumer для RabbitMQ
├── DOCUMENTATION.md           # Техническая документация
├── API_EXAMPLES.md            # Примеры использования API
└── requirements.txt           # Зависимости Python
```
