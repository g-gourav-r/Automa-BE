from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.user import PlatformUser, UserCredentials
from src.utils.security import hash_password, verify_password
from src.utils.jwt import create_access_token
from src.api.dependencies.auth import get_current_user
from src.core.config import get_db  # Now this is a sync session generator
from src.schemas.user import UserSignupRequest, UserLoginRequest

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    signup_data: UserSignupRequest,
    db: Session = Depends(get_db)
):
    result = db.execute(select(PlatformUser).filter(PlatformUser.email == signup_data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    hashed_password = hash_password(signup_data.password)
    new_user = PlatformUser(
        first_name=signup_data.first_name,
        last_name=signup_data.last_name,
        email=signup_data.email,
        company_id = signup_data.company_id or 1
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    credentials = UserCredentials(
        platform_user_id=new_user.platform_user_id,
        password_hash=hashed_password
    )
    db.add(credentials)
    db.commit()
    db.refresh(credentials)

    return {"message": "User registered successfully"}

@router.post("/login")
def login(
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    result = db.execute(select(PlatformUser).filter(PlatformUser.email == login_data.email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    result_credentials = db.execute(
        select(UserCredentials).filter(UserCredentials.platform_user_id == user.platform_user_id)
    )
    credentials = result_credentials.scalars().first()

    if not verify_password(login_data.password, credentials.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.platform_user_id})
    return {"access_token": access_token, "token_type": "bearer"}