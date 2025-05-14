import os
import logging
import cv2
import numpy as np
import pytesseract
import json
import openai
from src.core.config import settings
from PIL import Image
from pdf2image import convert_from_path
from src.core.config import get_db
from src.models import templates as templates_model

# Logging setup
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

def pdf_to_images(pdf_path: str) -> list[Image.Image]:
    """Convert each page of a PDF into a PIL Image list."""
    logger.info(f"Converting PDF to images: {pdf_path}")
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        logger.info(f"Converted {len(pages)} pages to images.")
        return pages
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Grayscale and threshold an image for better OCR."""
    logger.debug("Preprocessing image for OCR...")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def ocr_image(image: np.ndarray) -> str:
    """Run Tesseract OCR on a preprocessed image and return extracted text."""
    logger.debug("Running OCR on image...")
    try:
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"Error during OCR: {e}")
        raise


def annotate_image(image: np.ndarray, output_path: str) -> None:
    """Draw OCR bounding boxes onto the image and save to disk."""
    logger.debug(f"Annotating image and saving to {output_path}...")
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        n = len(data['text'])
        for i in range(n):
            if int(data['conf'][i]) > 0 and data['text'][i].strip():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imwrite(output_path, image)
        logger.info(f"Saved annotated image: {output_path}")
    except Exception as e:
        logger.error(f"Failed to annotate image: {e}")
        raise


def extract_key_values_with_ai(text: str, template_description: str) -> dict:
    """
    Use OpenAI to extract key-value pairs from OCR text guided by a human-provided description.
    Returns a JSON-like dict or a fallback message.
    """
    logger.debug("Extracting key-value pairs via AI...")

    prompt = f"""
You are an intelligent document data extraction AI.
The following text has been extracted via OCR (pytesseract) from a scanned document, and may contain errors.
A human-provided template description (which may have grammar or spelling mistakes) is given to help infer document type.

**Important Instructions:**
- Infer the document type from the description.
- Extract only clearly identifiable key-value pairs from the text relevant to that type.
- Do not guess values not present in the OCR text.
- If a field is uncertain, set its value to "N/A".
- If no meaningful key-value pairs found, return:
  {{ "message": "No relevant key-value pairs found." }}
- Respond with valid JSON only.

**Template Description:**
{template_description}

**OCR Text:**
{text}
"""

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        logger.debug("Sending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a strict JSON-outputting agent."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("AI returned invalid JSON.")
            logger.debug(f"AI content: {content}")
            return {"message": "AI response was not valid JSON."}
    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return {"message": "Failed to extract data using AI."}


def process_template(pdf_path: str, template_description: str) -> dict:
    """
    Full pipeline: PDF → images → preprocess → OCR → annotate → AI extraction.
    Returns a dict with page-level key-values and annotated paths.
    """
    logger.info(f"Processing PDF template: {pdf_path}")
    os.makedirs("output", exist_ok=True)

    try:
        pages = pdf_to_images(pdf_path)
        results = []

        for idx, page in enumerate(pages, start=1):
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            proc = preprocess_image(img)
            text = ocr_image(proc)

            annotated_path = f"output/annotated_page_{idx}.png"
            annotate_image(img, annotated_path)

            kv = extract_key_values_with_ai(text, template_description)
            results.append({
                "page": idx,
                "annotated_image": annotated_path,
                "key_values": kv
            })

        return {"pages": results}

    except Exception as e:
        logger.error(f"Error in process_template: {e}")
        raise


def save_template_to_db(company_id: int, created_by_user_id: int,
                        description: str, template_name: str,
                        template_data: dict) -> int:
    """
    Persist a Template record in the database and return its new ID.
    """
    session = get_db_session()
    try:
        new_t = templates_model.Template(
            company_id=company_id,
            created_by_user_id=created_by_user_id,
            description=description,
            template_format=template_data,
            template_name=template_name,
            visibility='personal'
        )
        session.add(new_t)
        session.commit()
        logger.info(f"Saved template ID {new_t.template_id} to DB.")
        return new_t.template_id
    except Exception as e:
        session.rollback()
        logger.error(f"DB save failed: {e}")
        raise
    finally:
        session.close()