import os
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import Annotated
from src.services import template_processing
from src.api.dependencies.auth import get_current_user
from src.models.user import PlatformUser

router = APIRouter()

@router.post("/create-template/")
async def create_template(
    file: Annotated[UploadFile, File()],
    template_name: Annotated[str, Form()],
    template_description: Annotated[str, Form()],
    current_user: PlatformUser = Depends(get_current_user)
):
    """
    Endpoint to upload a template file for OCR processing.
    Returns extracted text data for user confirmation before saving.
    """
    try:
        user_id = current_user.platform_user_id
        company_id = current_user.company_id
        print(f"User {user_id} from company {company_id} is uploading a template.")

        # Save uploaded file temporarily
        contents = await file.read()
        file_path = f"temp_{template_name}"
        with open(file_path, "wb") as f:
            f.write(contents)

        # Process file using Tesseract OCR service
        print(f"File saved at {file_path}, starting template processing...")
        template_data = template_processing.process_template(file_path, template_description)
        print("Template processing complete.")

        # Clean up temporary file
        os.remove(file_path)

        return JSONResponse(
            content={"message": "Template processed successfully", "template_data": template_data},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing template: {str(e)}")

@router.post("/save-template/")
async def save_template(
    template_data: Annotated[str, Form()],
    description: Annotated[str, Form()],
    template_name: Annotated[str, Form()],
    current_user: PlatformUser = Depends(get_current_user)
):
    """
    Endpoint to save template metadata and OCR result into the database after user confirmation.
    """
    try:
        user_id = current_user.platform_user_id
        company_id = current_user.company_id

        # Save to database
        template_id = template_processing.save_template_to_db(
            company_id=company_id,
            created_by_user_id=user_id,
            description=description,
            template_name=template_name,
            template_data=template_data
        )

        return JSONResponse(
            content={"message": "Template saved successfully", "template_id": template_id},
            status_code=201
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving template: {str(e)}")
