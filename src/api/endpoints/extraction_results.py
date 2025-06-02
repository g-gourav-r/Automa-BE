import logging
from typing import List

from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.template import (
    TemplateExtractionResultResponse,
    TemplateExtractionResultCreate
)
from src.services.extraction_result_service import (
    create_extraction_result,
)
from src.api.dependencies.auth import get_current_user
from src.core.config import get_db
from src.models.user import PlatformUser  # added for consistent typing

# Initialise logger for this module
logger = logging.getLogger(__name__)

# Create API router instance
router = APIRouter()


@router.post(
    "/add-extraction-result/",
    response_model=TemplateExtractionResultResponse,
    summary="Add a new template extraction result",
    status_code=status.HTTP_201_CREATED
)
async def add_extraction_result(
    extraction_result: TemplateExtractionResultCreate,
    current_user: PlatformUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Adds a new template extraction result into the database.

    Args:
        extraction_result (TemplateExtractionResultCreate): The extraction result data.
        current_user (PlatformUser): Authenticated user details.
        db (AsyncSession): SQLAlchemy async database session.

    Returns:
        TemplateExtractionResultResponse: The created extraction result.
    """
    try:
        result = await create_extraction_result(db, extraction_result)
        return result

    except Exception as e:
        logger.error(f"Error adding extraction result: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save extraction result: {str(e)}"
        )