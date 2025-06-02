import asyncio
import ssl
from typing import Optional

from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import text
from google.cloud.sql.connector import Connector, IPTypes

# Set up default SSL context
ssl_context = ssl.create_default_context()


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    INSTANCE_CONNECTION_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    JWT_SECRET_KEY: str
    STORAGE_BUCKET_NAME: str
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    ENV: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()


async def create_async_db_engine():
    """Create and return an asynchronous SQLAlchemy database engine."""
    connector = Connector()

    async def getconn():
        conn = await connector.connect_async(
            settings.INSTANCE_CONNECTION_NAME,
            "asyncpg",
            user=settings.DB_USER,
            password=settings.DB_PASS,
            db=settings.DB_NAME,
            ip_type=IPTypes.PUBLIC,
            loop=asyncio.get_running_loop()
        )
        return conn

    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=getconn,
        pool_pre_ping=True
    )
    return engine


async def get_db():
    """Yield an asynchronous database session with commit/rollback handling."""
    engine = await create_async_db_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()  # TODO:Disposing engine per call — fine for CLI tasks, reconsider for high-frequency app use


Base = declarative_base()
