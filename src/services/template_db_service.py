from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import templates, template_extraction_results
from src.schemas.template import TemplateListResponse, TemplateContentResponse, TemplateExtractionResultResponse
from typing import Optional, List
import json
import logging
from sqlalchemy.exc import NoResultFound

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def save_template_to_db(
    company_id: int,
    created_by_user_id: int,
    description: str,
    template_name: str,
    extraction_method: str,
    template_data: str,
    db_session: AsyncSession
) -> int:
    """
    Save a template’s metadata and structure to the database.

    Args:
        company_id (int): The company identifier.
        created_by_user_id (int): The user identifier who created the template.
        description (str): A description of the template.
        template_name (str): The name of the template.
        extraction_method (str): The method used for data extraction.
        template_data (str): JSON string representing the template structure.
        db_session (AsyncSession): The active database session.

    Returns:
        int: The unique ID of the newly saved template.
    """
    try:
        parsed_data = json.loads(template_data)

        new_template = templates.Template(
            company_id=company_id,
            created_by_user_id=created_by_user_id,
            description=description,
            template_format=parsed_data,
            template_name=template_name,
            visibility='personal',
            extraction_method=extraction_method,
        )

        db_session.add(new_template)
        await db_session.commit()
        await db_session.refresh(new_template)

        logger.info("Template saved successfully with ID: %s", new_template.template_id)
        return new_template.template_id

    except Exception as e:
        await db_session.rollback()
        logger.error("Failed to save template: %s", e)
        raise


async def get_all_templates_from_db(
    db_session: AsyncSession, 
    company_id: Optional[int] = None
) -> List[TemplateListResponse]:
    """
    Fetch all templates from the database, optionally filtered by company.

    Args:
        db_session (AsyncSession): The active database session.
        company_id (Optional[int]): The company ID to filter templates.

    Returns:
        List[TemplateListResponse]: A list of template summaries.
    """
    query = select(
        templates.Template.template_id,
        templates.Template.template_name,
        templates.Template.description,
    )

    if company_id is not None:
        query = query.where(templates.Template.company_id == company_id)

    result = await db_session.execute(query)

    templates_data = [
        TemplateListResponse(
            template_id=row.template_id,
            template_name=row.template_name,
            description=row.description
        )
        for row in result.fetchall()
    ]

    logger.info("Fetched %d template(s) from the database.", len(templates_data))
    return templates_data


async def get_template_content_from_db(
    db_session: AsyncSession, 
    template_id: int
) -> Optional[TemplateContentResponse]:
    """
    Retrieve the full content of a specific template by its ID.

    Args:
        db_session (AsyncSession): The active database session.
        template_id (int): The ID of the template to retrieve.

    Returns:
        Optional[TemplateContentResponse]: The template content if found, else None.
    """
    result = await db_session.execute(
        select(templates.Template).where(templates.Template.template_id == template_id)
    )
    template = result.scalars().first()

    if template:
        logger.info("Template content retrieved for template ID: %d", template_id)
        return TemplateContentResponse.from_orm(template)
    
    logger.warning("No template found with ID: %d", template_id)
    return None

async def get_template_entries_from_db(db_session: AsyncSession, template_id: int):
    """
    Fetch all extraction results for a specific template.

    Args:
        db_session (AsyncSession): SQLAlchemy async database session.
        template_id (int): ID of the template.

    Returns:
        List[TemplateExtractionResultResponse]: List of extraction results.
    """
    result = await db_session.execute(
        select(template_extraction_results.TemplateExtractionResult).where(template_extraction_results.TemplateExtractionResult.template_id == template_id)
    )
    entries = result.scalars().all()
    return entries


async def get_template_metadata( template_id: int, db_session: AsyncSession) -> Optional[TemplateContentResponse]:
    """
    Fetch template metadata by template_id.

    Args:
        template_id (int): ID of the template to fetch.
        db_session (AsyncSession): Async SQLAlchemy session.

    Returns:
        Template object or None if not found.
    """

    # Query the template filtering by template_id
    stmt = select(templates.Template).where(templates.Template.template_id == template_id)

    try:
        result = await db_session.execute(stmt)
        template = result.scalar_one()  # Raises if none or multiple results
        return TemplateContentResponse.from_orm(template)

    except NoResultFound:
        return None