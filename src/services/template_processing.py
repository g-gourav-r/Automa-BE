import os
import logging
import cv2
import numpy as np
import pytesseract
import re
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
    logger.info(f"Converting PDF to images: {pdf_path}")
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        logger.info(f"Converted {len(pages)} pages to images.")
        return pages
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise

def preprocess_image(image: np.ndarray) -> np.ndarray:
    logger.debug("Preprocessing image for OCR...")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def ocr_image(image: np.ndarray) -> str:
    logger.debug("Running OCR on image...")
    try:
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"Error during OCR: {e}")
        raise

def extract_word_positions(image: np.ndarray) -> list[dict]:
    """
    Extract word-level positions from image using pytesseract.
    Returns a list of dicts with text and bounding box info.
    """
    logger.debug("Extracting word positions from image...")
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        positions = []
        n = len(data['text'])
        for i in range(n):
            if int(data['conf'][i]) > 0 and data['text'][i].strip():
                positions.append({
                    "text": data['text'][i],
                    "x": data['left'][i],
                    "y": data['top'][i],
                    "w": data['width'][i],
                    "h": data['height'][i]
                })
        logger.info(f"Extracted {len(positions)} word positions.")
        return positions
    except Exception as e:
        logger.error(f"Failed to extract word positions: {e}")
        raise

def annotate_image(image: np.ndarray, output_path: str) -> None:
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
import cv2
import os

def annotate_from_ai_response(image: np.ndarray, ai_response: dict, output_path: str) -> None:
    """
    Draw bounding boxes and labels on the image based on AI response key_values.

    :param image: The image as a numpy array.
    :param ai_response: The AI response containing 'key_values' list with positions.
    :param output_path: The path to save the annotated image.
    """
    try:
        annotated_image = image.copy()

        key_values = ai_response.get("key_values", [])
        if not key_values:
            logger.warning("No key_values found in AI response.")
            return

        for item in key_values:
            key = item.get("key")
            pos = item.get("position")
            if not key or not pos:
                logger.warning(f"Invalid key_value item: {item}")
                continue

            x, y, w, h = pos.get("x"), pos.get("y"), pos.get("w"), pos.get("h")
            if None in (x, y, w, h):
                logger.warning(f"Incomplete position data: {pos}")
                continue

            # Draw rectangle
            cv2.rectangle(annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Put label text above the rectangle
            font_scale = 0.5
            thickness = 1
            (text_width, text_height), _ = cv2.getTextSize(key, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_x = x
            text_y = y - 5 if y - 5 > 10 else y + text_height + 5

            cv2.rectangle(annotated_image, (text_x - 2, text_y - text_height - 2),
                          (text_x + text_width + 2, text_y + 2), (0, 255, 0), -1)

            cv2.putText(annotated_image, key, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, annotated_image)
        logger.info(f"Annotated image saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to annotate image from AI response: {e}")
        raise


def extract_key_values_with_ai(text: str, word_positions: list[dict], template_description: str) -> dict:
    """
    Use OpenAI to extract key-value pairs from OCR text and word positions guided by a human-provided description.
    AI infers document fields and returns key-value pairs along with bounding box positions.
    """
    logger.debug("Extracting key-value pairs via AI with word positions...")

    prompt = f"""
You are an intelligent document data extraction AI.
The following text has been extracted via OCR from a scanned document, which may contain errors.
A human-provided template description is given to help infer document type and expected fields.

**Important Instructions:**
- Infer the document type from the description.
- Extract key-value pairs from the text.
- Use the provided word positions to group multi-line fields like addresses (combine consecutive words/lines if relevant).
- Even if headings like "Office Address" aren't explicitly in the OCR text, infer them based on context and template.
- For each extracted key-value pair, also return the combined bounding box (x, y, width, height) for the value text.
- If a field is uncertain or value missing, set its value to "N/A".
- If no relevant key-value pairs are found, return:
  {{ "message": "No relevant key-value pairs found." }}
- Respond ONLY with valid JSON in this structure:

{{
  "key_values": [
    {{
      "key": "Invoice Number",
      "value": "123456",
      "position": {{ "x": 100, "y": 200, "w": 150, "h": 30 }}
    }},
    ...
  ]
}}

**Template Description:**
{template_description}

**OCR Text:**
{text}

**Word Positions:**
{json.dumps(word_positions, indent=2)}
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
        # Remove possible ```json or ``` wrappers
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        logger.debug(f"AI response content: {content}")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("AI returned invalid JSON.")
            return {"message": "AI response was not valid JSON."}
    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return {"message": "Failed to extract data using AI."}

def process_template(pdf_path: str, template_description: str) -> dict:
    logger.info(f"Processing PDF template: {pdf_path}")
    os.makedirs("output", exist_ok=True)

    try:
        pages = pdf_to_images(pdf_path)
        results = []

        for idx, page in enumerate(pages, start=1):
            logger.info(f"Processing page {idx}")
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            proc = preprocess_image(img)
            text = ocr_image(proc)
            word_positions = extract_word_positions(img)

            # Basic OCR annotation image
            annotated_path = f"temp_annotate/annotated_page_{idx}.png"
            # annotate_image(img, annotated_path)

            # AI key-value extraction
            ai_result = extract_key_values_with_ai(text, word_positions, template_description)

            # If AI extraction contains annotations (or positional data), draw AI-based annotations
            ai_annotated_path = f"temp_annotated/ai_annotated_page_{idx}.png"
            if ai_result.get("key_values"):
                annotate_from_ai_response(img, ai_result, ai_annotated_path)

                logger.info(f"AI annotated image for page {idx} saved.")
            else:
                ai_annotated_path = None
                logger.info(f"No AI annotations found for page {idx}.")

            results.append({
                "page": idx,
                "annotated_image": annotated_path,
                "ai_extraction": ai_result,
                "ai_annotated_image": ai_annotated_path
            })

        return {"pages": results}

    except Exception as e:
        logger.error(f"Error in process_template: {e}")
        raise

def save_template_to_db(company_id: int, created_by_user_id: int,
                        description: str, template_name: str,
                        template_data: dict) -> int:
    session = get_db()
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
