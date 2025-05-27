import logging
from typing import Annotated, List

from fastapi import APIRouter, Form, Depends, HTTPException, status, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import PlatformUser
from src.services.template_db_service import (
    save_template_to_db,
    get_all_templates_from_db,
    get_template_content_from_db,
    get_template_entries_from_db
)
from src.api.dependencies.auth import get_current_user
from src.core.config import get_db
from src.schemas.template import TemplateListResponse, TemplateContentResponse, TemplateExtractionResultResponse

# Initialise logger for this module
logger = logging.getLogger(__name__)

# Create API router instance
router = APIRouter()


@router.post("/save-template/")
async def save_template(
    template_data: Annotated[str, Form()],
    description: Annotated[str, Form()],
    template_name: Annotated[str, Form()],
    extraction_method: Annotated[str, Form()],
    current_user: PlatformUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save template metadata and processed OCR result into the database
    after user confirmation.

    Args:
        template_data (str): The extracted template data.
        description (str): Template description.
        template_name (str): Name of the template.
        extraction_method (str): Method used for extraction.
        current_user (PlatformUser): Authenticated user details.
        db (AsyncSession): SQLAlchemy async database session.

    Returns:
        JSONResponse: Success message and template ID.
    """
    try:
        user_id = current_user.platform_user_id
        company_id = current_user.company_id

        template_id = await save_template_to_db(
            company_id=company_id,
            created_by_user_id=user_id,
            description=description,
            template_name=template_name,
            template_data=template_data,
            extraction_method=extraction_method,
            db_session=db
        )

        return JSONResponse(
            content={"message": "Template saved successfully", "template_id": template_id},
            status_code=201
        )

    except Exception as e:
        logger.error(f"Error saving template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error saving template: {str(e)}")


@router.get(
    "/list-templates/",
    response_model=List[TemplateListResponse],
    summary="List all available templates",
    status_code=status.HTTP_200_OK
)
async def list_templates(
    current_user: PlatformUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TemplateListResponse]:
    """
    Retrieve a list of all templates accessible by the current user.

    Args:
        current_user (PlatformUser): Authenticated user details.
        db (AsyncSession): SQLAlchemy async database session.

    Returns:
        List[TemplateListResponse]: List of available templates.
    """
    try:
        templates = await get_all_templates_from_db(db_session=db)
        return templates

    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve templates: {str(e)}"
        )


@router.get(
    "/get-template/{template_id}",
    response_model=TemplateContentResponse,
    summary="Get content of a specific template by ID",
    status_code=status.HTTP_200_OK
)
async def get_template_content(
    template_id: int = Path(..., description="The ID of the template to retrieve"),
    current_user: PlatformUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TemplateContentResponse:
    """
    Retrieve the content of a specific template identified by its ID.

    Args:
        template_id (int): ID of the template.
        current_user (PlatformUser): Authenticated user details.
        db (AsyncSession): SQLAlchemy async database session.

    Returns:
        TemplateContentResponse: Template content details.
    """
    try:
        template_content = await get_template_content_from_db(
            db_session=db,
            template_id=template_id
        )

        if not template_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found."
            )

        return template_content

    except HTTPException as http_exc:
        raise http_exc  # Re-raise known HTTP exceptions
    except Exception as e:
        logger.error(f"Error retrieving template content for ID {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve template content: {str(e)}"
        )

@router.get(
    "/{template_id}/entries",
    response_model=List[TemplateExtractionResultResponse],
    summary="Get all entries for a specific template",
    status_code=status.HTTP_200_OK
)
async def get_template_entries(
    template_id: int = Path(..., description="The ID of the template to retrieve entries for"),
    current_user: PlatformUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TemplateExtractionResultResponse]:
    """
    Retrieve all entries associated with a given template.

    Args:
        template_id (int): ID of the template.
        current_user (PlatformUser): Authenticated user details.
        db (AsyncSession): SQLAlchemy async database session.

    Returns:
        List[TemplateEntryResponse]: List of template entries.
    """
    try:
        entries = await get_template_entries_from_db(db_session=db, template_id=template_id)

        if not entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entries found for template ID {template_id}."
            )

        return entries

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error retrieving entries for template ID {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve template entries: {str(e)}"
        )
