from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user import PlatformUser
from src.api.dependencies.auth import get_current_user
from src.core.config import get_db
from src.models.user import Company
from sqlalchemy.orm import selectinload

router = APIRouter()

@router.get("/profile")
async def get_user_profile(
    current_user: PlatformUser = Depends(get_current_user),  # Extracts user from the token
    db: AsyncSession = Depends(get_db)
):
    # Fetch the user along with the company data using a relationship loading technique like selectinload
    result = await db.execute(
        select(PlatformUser)
        .options(selectinload(PlatformUser.company))  # Load the related company data
        .filter(PlatformUser.platform_user_id == current_user.platform_user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Prepare the response, including company_name from the related company object
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "company_id": user.company_id,
        "company_name": user.company.company_name,  # Accessing company name from the relationship
    }
