from datetime import datetime, timedelta
from fastapi import HTTPException
from src.core.config import settings  # Assuming the secret key is in the config
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from jwt.exceptions import DecodeError, InvalidSignatureError, InvalidTokenError
import logging

# Setup logger
logger = logging.getLogger(__name__)

SECRET_KEY = settings.JWT_SECRET_KEY  # You can put a different secret key for JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expires after 30 minutes


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generates an access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = data.copy()

    # Ensure 'sub' is a string
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodes the access token."""
    try:
        # Attempt to decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except InvalidSignatureError:
        logger.error("Invalid token signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
        )
    except DecodeError as e:
        logger.error(f"DecodeError: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token encoding or padding. Check token format.  Details: {e}",
        )
    except InvalidTokenError as e:
        logger.error(f"InvalidTokenError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or malformed token: {e}",
        )
    except JWTError as e:
        logger.error(f"JWTError: {e}, args: {e.args}", exc_info=True) #Include exc_info
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid token: {e}"
        )
    except Exception as e:
        logger.error(f"Error decoding token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token decoding",
        )