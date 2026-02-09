"""FastAPI приложение для управления заказами.

Основное приложение, содержащее:
- Маршруты для аутентификации и управления заказами
- Middleware для обработки токенов и CORS
- Обработчик rate limiting
"""

from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.routers.auth import auth_router
from app.routers.order import order_router
from app.security import check_token, limiter


app = FastAPI(title="Order management")


@app.get('/health')
async def welcome():
    """Проверка здоровья приложения.
    
    Returns:
        str: Приветственное сообщение
    """
    return 'Welcome to Order Management!'


origins = ["*"]  
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )


@app.middleware("http")
async def set_user_id_middleware(request: Request, call_next):
    """Middleware для извлечения и проверки JWT токена из заголовка Authorization.
    
    Данный middleware:
    - Извлекает токен из заголовка Authorization (формат: Bearer <token>)
    - Проверяет валидность токена
    - Сохраняет ID пользователя в request.state для использования в маршрутах
    
    Args:
        request: Объект запроса
        call_next: Функция для передачи управления следующему обработчику
        
    Returns:
        Response: Ответ от следующего обработчика
    """
    user_id: int | None = None
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            user_id = await check_token(token=token)
        except (HTTPException, Exception):
            user_id = None 
    request.state.user_id = user_id
    response = await call_next(request)
    return response


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.include_router(auth_router)
app.include_router(order_router)


