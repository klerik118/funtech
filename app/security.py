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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token",scheme_name="JWT Token")


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def check_token(token: str = Depends(oauth2_scheme)) -> Optional[int]:
    try:
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
    user_id = await UserRepository.checking_user_id(session, id)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='This user does not exist')
    return user_id
   

async def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user_or_ip_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return f"user_{user_id}"
    ip = request.client.host or "unknown"
    return f"anon_{ip}"


limiter = Limiter(key_func=get_user_or_ip_key, storage_uri=REDIS_URL_RATE_LIMIT)
