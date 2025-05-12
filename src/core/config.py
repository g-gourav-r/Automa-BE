from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from google.cloud.sql.connector import Connector, IPTypes
import ssl

ssl_context = ssl.create_default_context()

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    INSTANCE_CONNECTION_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    class Config:
        env_file = ".env"

settings = Settings()

def create_db_engine():
    connector = Connector()
    def getconn():
        conn = connector.connect(
            settings.INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=settings.DB_USER,
            password=settings.DB_PASS,
            db=settings.DB_NAME,
            ip_type=IPTypes.PUBLIC
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_db_engine())
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    engine = create_db_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 'Configuration is working!'"))
            message = result.scalar_one()
            print(message)
    except Exception as e:
        print(f"Error connecting to database: {e}")
    finally:
        if 'connector' in locals() and connector:
            connector.close()