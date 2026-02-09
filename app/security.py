"""Модуль безопасности за цальестью выполнения приложения.

Занимается следующим:
- JWT токен оверификация и проверка
- Кодирование и верификация паролей
- Rate limiting для защиты от атак
"""

from typing import Optional

from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status
from fastapi import Depends, status
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from slowapi import Limiter

from app.core.config import auth
from app.database.database import get_async_session
from app.repositories.user import UserRepository
from app.core.config import REDIS_URL_RATE_LIMIT


# OAuth2 схема для JWT токенов
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token",scheme_name="JWT Token")


# Настройка контекста для хеширования паролей галгоритмом argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def check_token(token: str = Depends(oauth2_scheme)) -> Optional[int]:
    """Проверить JWT токен и выставить ожидание Юзера.
    
    Args:
        token: JWT токен для проверки
        
    Returns:
        int: ID пользователя из токена
        
    Raises:
        HTTPException: При истечении, неверности токена или инвалидной подписи
    """
    try:
        # Декодируем токен с помощью публичного ключа
        decod = jwt.decode(token, auth.public_key_path.read_text(), algorithms=[auth.algorithm]) 
        id: str = decod.get('sub')
        if not id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect data')
        return int(id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Expired token') 
    except (jwt.InvalidTokenError, jwt.DecodeError, jwt.InvalidSignatureError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid token: {str(e)}')


async def get_id_current_user(
        id: int = Depends(check_token), 
        session: AsyncSession = Depends(get_async_session)
        ) -> Optional[int]:
    """Получить ID текущего автентифицированного пользователя и проверить его существование.
    
    Args:
        id: ID из токена
        session: Async сессия BD
        
    Returns:
        int: ID реально существующего пользователя
        
    Raises:
        HTTPException: Пользователь не понайден в BD
    """
    user_id = await UserRepository.checking_user_id(session, id)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='This user does not exist')
    return user_id
   

async def hash_password(password: str) -> str:
    """По сообщивчи данный пароль через argon2.
    
    Args:
        password: Открытый пароль
        
    Returns:
        str: Эшированный пароль
    """
    return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Открытый пароль с женахированным.
    
    Args:
        plain_password: Открытый пароль
        hashed_password: Эшированный пароль
        
    Returns:
        bool: True если эшированные равны, False в противном случае
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user_or_ip_key(request: Request) -> str:
    """Определить ключ используя для rate limiting: ID автентифицированного пользователя или IP-адрес анонимного.
    
    Args:
        request: Объект запроса
        
    Returns:
        str: Ключ для identifikator-a rate limitа
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return f"user_{user_id}"
    ip = request.client.host or "unknown"
    return f"anon_{ip}"


# Конфигурация rate limiter с Redis бекэндом
limiter = Limiter(key_func=get_user_or_ip_key, storage_uri=REDIS_URL_RATE_LIMIT)
