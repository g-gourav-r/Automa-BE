import os
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated
from src.services import invoice_processing

router = APIRouter()

@router.post("/parse_invoice/")
async def parse_invoice(file: Annotated[UploadFile, File()]):
    """
    Endpoint to upload a PDF invoice and receive structured data as JSON.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        contents = await file.read()
        with open("temp_invoice.pdf", "wb") as f:
            f.write(contents)
        pdf_path = "temp_invoice.pdf"
        structured_data = invoice_processing.process_pdf(pdf_path)
        os.remove(pdf_path)  # Clean up temporary file
        return JSONResponse(content=structured_data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")