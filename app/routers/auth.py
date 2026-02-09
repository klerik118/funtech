"""Маршруты автентификации и регистрации пользователей.

Обработывает:
- Пост регистрации новых пользователей
- Получение JWT токенов
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import jwt

from app.database.database import get_async_session
from app.schemas import UserRegister
from app.repositories.user import UserRepository
from app.security import hash_password, verify_password
from app.core.config import auth


auth_router = APIRouter(tags=['Registration/Authorization'])


@auth_router.post('/register/', summary='Registration with email confirmation', response_model=dict) 
async def registration_user(new_user: UserRegister, session: AsyncSession = Depends(get_async_session)):
    """Регистрация нового пользователя.
    
    Args:
        new_user: Данные нового пользователя (электронная почта, пароль)
        session: Асинхронная сессия BD
        
    Returns:
        dict: Подтверждение регистрации
        
    Raises:
        HTTPException: Пользователь с этим электронным адресом уже регистрирован
    """
    if await UserRepository.check_for_user_existence(session, new_user.email):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A user with this email is already registered"
            )
    hashed_password = await hash_password(new_user.password)
    await UserRepository.adding_user(session, new_user.email.lower(), hashed_password)
    return {'status': f'User with email {new_user.email} successfully added'}


@auth_router.post('/token', summary='Login', response_model=dict) 
async def user_login(user: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_async_session)):
    """Ответить JWT токен для автентифицированного пользователя.
    
    Args:
        user: Креденциалы пользователя (электронная почта, пароль)
        session: Асинхронная сессия BD
        
    Returns:
        dict: JWT токен для использования в поля "Authorization: Bearer <token>"
        
    Raises:
        HTTPException: Пользователь не найден или неверные креденациалы
    """
    user_from_db = await UserRepository.get_user_by_email(session, user.username.lower())
    if not user_from_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="There is no user with this email"
            )
    if (
        user.username.lower() == user_from_db.email 
        and await verify_password(user.password, user_from_db.hashed_password)
        ):
        # Сождаю JWT токен с приватным ключом
        private_key = auth.private_key_path.read_text()  
        expire = datetime.now(timezone.utc) + timedelta(minutes=auth.expiration)
        payload = {"sub": str(user_from_db.id), "exp": expire}
        encode_jwt = jwt.encode(payload, private_key, algorithm=auth.algorithm)
        return {"access_token": encode_jwt, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid password')