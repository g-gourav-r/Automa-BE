from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.template import TemplateExtractionResultCreate
from src.models.template_extraction_results import TemplateExtractionResult
from typing import List
from sqlalchemy import select
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def create_extraction_result(
    db: AsyncSession, 
    extraction_result_data: TemplateExtractionResultCreate
) -> TemplateExtractionResult:
    """
    Create and store a new extraction result record in the database.

    Args:
        db (AsyncSession): The active asynchronous database session.
        extraction_result_data (TemplateExtractionResultCreate): The data for the new extraction result.

    Returns:
        TemplateExtractionResult: The newly created extraction result record.
    """
    try:
        new_result = TemplateExtractionResult(
            template_id=extraction_result_data.template_id,
            source_file_name=extraction_result_data.source_file_name,
            parsed_data=extraction_result_data.parsed_data
        )
        db.add(new_result)
        await db.commit()
        await db.refresh(new_result)

        logger.info("Created extraction result with ID: %s for template ID: %s",
                    new_result.result_id, new_result.template_id)
        return new_result

    except Exception as e:
        await db.rollback()
        logger.error("Failed to create extraction result: %s", e)
        raise