import os
import logging
import numpy as np
import cv2

from src.services.pdf_service import pdf_to_images
from src.services.ocr_service import preprocess_image, ocr_image, extract_word_positions
from src.services.ai_extraction_service import extract_key_values_with_ai, extract_key_values_with_ai_for_template
from src.services.annotation_service import annotate_from_ai_response
from src.services.gcs_service import upload_to_gcs
from src.core.config import settings

logger = logging.getLogger(__name__)
bucket_name = settings.STORAGE_BUCKET_NAME

async def process_template(
    pdf_path: str,
    template_description: str,
    user_id: int,
    company_id: int
) -> dict:
    """Main orchestration: process PDF → OCR → AI extraction → annotate → upload."""
    logger.info(f"Starting template processing for: {pdf_path}")

    os.makedirs("temp", exist_ok=True)
    results = []

    try:
        pages = pdf_to_images(pdf_path)

        for idx, page in enumerate(pages, start=1):
            logger.info(f"Processing page {idx}")
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

            proc_img = preprocess_image(img)
            text = ocr_image(proc_img)
            word_positions = extract_word_positions(img)

            ai_result = extract_key_values_with_ai(text, word_positions, template_description)

            annotated_path = f"temp/ai_annotated_page_{idx}.png"
            signed_url = None

            if ai_result.get("key_values"):
                annotate_from_ai_response(img, ai_result, annotated_path)
                logger.info(f"Annotated page {idx} saved locally.")

                destination_blob_name = f"ai_annotated_page_{idx}.png"
                signed_url = upload_to_gcs(
                    company_id=company_id,
                    user_id=user_id,
                    source_file_path=annotated_path,
                    destination_blob_name=destination_blob_name
                )
                logger.info(f"Annotated page {idx} uploaded to cloud.")

            results.append({
                "page": idx,
                "ai_extraction": ai_result,
                "ai_annotated_image_url": signed_url
            })

        return {"pages": results}

    except Exception as e:
        logger.error(f"Error processing template: {e}")
        raise

async def extract_data_using_template(file_path, template_description, template_parsed_data, user_id, company_id):
    """Main orchestration: process PDF → OCR → AI extraction → annotate → upload."""
    logger.info(f"Starting template processing for: {file_path}")

    os.makedirs("temp", exist_ok=True)
    results = []
    try:
        pages = pdf_to_images(file_path)

        for idx, page in enumerate(pages, start=1):
            logger.info(f"Processing page {idx}")
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

            proc_img = preprocess_image(img)
            text = ocr_image(proc_img)
            word_positions = extract_word_positions(img)

            ai_result = extract_key_values_with_ai_for_template(text, word_positions, template_description, template_parsed_data)

            annotated_path = f"temp/ai_annotated_page_{idx}.png"
            signed_url = None

            if ai_result.get("key_values"):
                annotate_from_ai_response(img, ai_result, annotated_path)
                logger.info(f"Annotated page {idx} saved locally.")

                destination_blob_name = f"ai_annotated_page_{idx}.png"
                signed_url = upload_to_gcs(
                    company_id=company_id,
                    user_id=user_id,
                    source_file_path=annotated_path,
                    destination_blob_name=destination_blob_name
                )
                logger.info(f"Annotated page {idx} uploaded to cloud.")

            results.append({
                "page": idx,
                "ai_extraction": ai_result,
                "ai_annotated_image_url": signed_url
            })

        return {"pages": results}

    except Exception as e:
        logger.error(f"Error processing template: {e}")
        raise