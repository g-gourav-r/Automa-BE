import os
import logging
from typing import Annotated

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession


from src.models.user import PlatformUser
from src.services.template_processing import process_template, extract_data_using_template
from src.services.template_db_service import get_template_metadata
from src.api.dependencies.auth import get_current_user
from src.schemas.template import TemplateExtractionResultCreate
from src.services.extraction_result_service import create_extraction_result


from src.core.config import get_db

# Initialise logger for this module
logger = logging.getLogger(__name__)

# Create API router instance
router = APIRouter()

@router.post("/create-template/")
async def create_template(
    file: Annotated[UploadFile, File()],
    template_name: Annotated[str, Form()],
    template_description: Annotated[str, Form()],
    current_user: PlatformUser = Depends(get_current_user)
):
    """
    Upload a template file for OCR processing.
    Returns extracted text data for user confirmation before saving.

    Args:
        file (UploadFile): Uploaded template file.
        template_name (str): Name of the template.
        template_description (str): Description of the template.
        current_user (PlatformUser): Authenticated user info (via dependency).

    Returns:
        JSONResponse: Processed template data or error message.
    """
    try:
        # Extract user and company identifiers
        user_id = current_user.platform_user_id
        company_id = current_user.company_id
        logger.info(f"User {user_id} from company {company_id} is uploading a template.")

        # Read uploaded file content
        contents = await file.read()

        # Define temporary file path
        file_path = f"temp_{template_name}"
        
        # Save file temporarily on disk
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"File saved at {file_path}. Starting template processing...")

        # Process file using Tesseract OCR service
        template_data = await process_template(file_path, template_description, user_id, company_id)
        logger.info("Template processing complete.")

        # Clean up temporary file after processing
        os.remove(file_path)
        logger.debug(f"Temporary file {file_path} removed.")

        # Return processed template data
        return JSONResponse(
            content={
                "message": "Template processed successfully",
                "template_data": template_data
            },
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error processing template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing template: {str(e)}")


@router.post("/{template_id}/upload")
async def create_template_to_data(
    template_id: int,
    file: Annotated[UploadFile, File()],
    current_user: PlatformUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint to upload a file and extract structured key-value data based on a predefined template.

    - Accepts a file upload and template ID.
    - Retrieves the template description and expected key structure from the database.
    - Runs OCR data extraction against the uploaded file using the template definition.
    - Merges extracted key-value pairs from multiple pages, ensuring each expected key is filled
      with the first available non-"N/A" value found.
    - Returns the fully populated extraction result as JSON.

    Parameters:
        template_id (int): ID of the template to be applied for extraction.
        file (UploadFile): File uploaded by the client for processing.
        current_user (PlatformUser): Authenticated user initiating the request.
        db (AsyncSession): Asynchronous database session.

    Returns:
        JSON containing the merged extracted key-value pairs as per the template description.
    """
    try:
        # Extract user and company identifiers
        user_id = current_user.platform_user_id
        company_id = current_user.company_id
        logger.info(f"User {user_id} from company {company_id} uploading file to template ID: {template_id}")

        # Read uploaded file content
        contents = await file.read()

        # Define temporary file path
        file_path = f"temp_{template_id}_{file.filename}"

        # Save file temporarily on disk
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"File saved at {file_path}. Starting template processing...")

        # Retrieve template metadata
        template_metadata = await get_template_metadata(template_id, db_session=db)
        if not template_metadata:
            raise HTTPException(status_code=404, detail="Template not found")
        print(template_metadata)

        template_description = template_metadata.template_description
        template_parsed_data = template_metadata.template_format

        # Process file using Tesseract OCR service
        template_data = await extract_data_using_template(
            file_path, template_description, template_parsed_data, user_id, company_id
        )
        logger.info("Template processing complete.")


        # Clean up temporary file after processing
        os.remove(file_path)
        logger.debug(f"Temporary file {file_path} removed.")

        print(template_data)

        # Extract pages from OCR result
        pages = template_data.get("pages", [])

        # Get list of expected keys from the template_parsed_data (template_format)
        expected_keys = list(template_parsed_data.keys())

        # Prepare a dictionary to hold the merged result with default "N/A" values
        merged_key_values = {key: {"key": key, "value": "N/A", "position": None} for key in expected_keys}

        # Go through all pages and fill in values where available
        for page in pages:
            key_values = page.get("ai_extraction", {}).get("key_values", [])
            for kv in key_values:
                key = kv.get("key")
                value = kv.get("value")
                position = kv.get("position")

                # Only update if the value isn't "N/A" and current stored value is "N/A"
                if key in merged_key_values and value != "N/A" and merged_key_values[key]["value"] == "N/A":
                    merged_key_values[key] = {"key": key, "value": value, "position": position}

        # Final extracted result as a list
        final_key_values = list(merged_key_values.values())

        # Flatten the extracted key-values into a simple dictionary
        flattened_extracted_result = {
            kv["key"]: kv["value"] 
            for kv in final_key_values
        }


        logger.debug(f"Merged extracted data: {flattened_extracted_result}")

        # Now, save to DB using your service function:
        extraction_create_obj = TemplateExtractionResultCreate(
            template_id=template_id,
            source_file_name=file.filename,
            parsed_data=flattened_extracted_result  # storing the full extraction result JSON
        )

        saved_result = await create_extraction_result(db, extraction_create_obj)

        # Return saved result as response (or modify to suit your response schema)
        return saved_result

    except Exception as e:
        logger.error(f"Error during template data extraction: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during file processing.")
