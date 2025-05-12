# utils/jwt.py
from datetime import datetime, timedelta
import jwt
from src.core.config import settings  # Assuming the secret key is in the config

SECRET_KEY = settings.OPENAI_API_KEY  # You can put a different secret key for JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expires after 30 minutes

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generates an access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodes the access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload if payload["exp"] >= datetime.utcnow().timestamp() else None
    except jwt.PyJWTError:
        return None
