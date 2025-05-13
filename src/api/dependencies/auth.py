from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.user import PlatformUser
from src.utils.jwt import decode_access_token
from src.core.config import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Initialize HTTPBearer to handle token extraction from request headers
bearer_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: AsyncSession = Depends(get_db)) -> PlatformUser:
    """
    Dependency to get the current authenticated user based on the JWT token.
    """
    # Extract token from the Authorization header
    token = credentials.credentials  # This is the actual JWT token
    token = token.replace("Bearer ", "") 

    # Decode the token to get the payload (user info)
    payload = decode_access_token(token)
    
    if payload is None:
        # If the token is invalid or expired, raise an Unauthorized error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Extract user ID from the payload (assuming 'sub' is the user ID in your token)
    user_id = int(payload.get("sub"))
    
    # Query the database for the user based on the user ID
    query = select(PlatformUser).filter(PlatformUser.platform_user_id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if user is None:
        # If the user is not found in the database, raise an Unauthorized error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user  # Return the PlatformUser object
