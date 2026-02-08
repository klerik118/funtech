import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

DB_HOST = os.environ.get('POSTGRES_HOST')
DB_PORT = os.environ.get('POSTGRES_PORT')
DB_NAME = os.environ.get('POSTGRES_DB')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

REDIS_URL = os.environ.get('REDIS_URL')
REDIS_URL_RATE_LIMIT = os.environ.get('REDIS_URL_RATE_LIMIT')
REDIS_URL_CELERY = os.environ.get('REDIS_URL_CELERY')

RABBITMQ_URL = os.environ.get('RABBITMQ_URL')

BASE_DIR = Path(__file__).parent.parent.parent

class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / ".secret_key" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / ".secret_key" / "jwt-public.pem"
    algorithm: str = "RS256"
    expiration: int = 60

auth = AuthJWT()