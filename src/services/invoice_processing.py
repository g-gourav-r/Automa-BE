import json
import numpy as np
import cv2
import pytesseract
import openai
from pdf2image import convert_from_path
from src.core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

def pdf_to_images(pdf_path: str, dpi: int = 300):
    """Convert each PDF page to a PIL Image at the specified DPI."""
    logger.info(f"Converting PDF to images: {pdf_path} with DPI {dpi}")
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        logger.info(f"Successfully converted {len(images)} pages to images.")
        return images
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        raise

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Grayscale, threshold, and clean up an image for better OCR accuracy."""
    logger.debug("Preprocessing image for OCR accuracy.")
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        logger.debug("Image preprocessing completed successfully.")
        return thresh
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        raise

def ocr_image(image: np.ndarray) -> str:
    """Extract text from a preprocessed image using Tesseract."""
    logger.debug("Running OCR on the image.")
    try:
        text = pytesseract.image_to_string(image)
        logger.debug("OCR completed successfully.")
        return text
    except Exception as e:
        logger.error(f"Error during OCR process: {str(e)}")
        raise

def extract_structured_data(text: str) -> dict:
    """
    Parses raw OCR text of an invoice into a structured JSON object.
    """
    logger.info("Extracting structured data from OCR text.")
    schema_str = """
{
  "basic_information": {
    "invoice_number": "string | null",
    "invoice_date": "MM-DD-YYYY | null",
    "due_date": "MM-DD-YYYY | null",
    "currency": "ISO_code | null",
    "po_number": "string | null",
    "payment_terms": "string | null",
    "confidence_score": {
      "invoice_number": "float | null",
      "invoice_date": "float | null",
      "due_date": "float | null",
      "currency": "float | null",
      "po_number": "float | null",
      "payment_terms": "float | null"
    }
  },
  "party_details": {
    "vendor": {
      "name": "string | null",
      "address": "string | null",
      "tax_id": "string | null",
      "contact": "string | null",
      "confidence_score": {
        "name": "float | null",
        "address": "float | null",
        "tax_id": "float | null",
        "contact": "float | null"
      }
    },
    "payer": {
      "name": "string | null",
      "address": "string | null",
      "reference": "string | null",
      "confidence_score": {
        "name": "float | null",
        "address": "float | null",
        "reference": "float | null"
      }
    }
  },
  "line_items": [
    {
      "description": "string | null",
      "quantity": "float | null",
      "unit_price": "float | null",
      "total": "float | null",
      "tax_rate": "float | null",
      "sku": "string | null",
      "category": "string | null",
      "confidence_score": {
        "description": "float | null",
        "quantity": "float | null",
        "unit_price": "float | null",
        "total": "float | null",
        "tax_rate": "float | null",
        "sku": "float | null",
        "category": "float | null"
      }
    }
  ],
  "grouped_data": {
    "by_tax_rate": {
      "0%": { "subtotal": "float | null", "items": "[integer] | null" },
      "10%": { "subtotal": "float | null", "items": "[integer] | null" }
    },
    "by_category": {
      "category_name": { "subtotal": "float | null", "items": "[integer] | null" }
    }
  },
  "totals": {
    "subtotal": "float | null",
    "taxes": {
      "0%": "float | null",
      "10%": "float | null"
    },
    "discount": "float | null",
    "shipping": "float | null",
    "grand_total": "float | null",
    "validation_warning": "string | null"
  },
  "metadata": {
    "source_file_type": "string | null",
    "ocr_confidence": "float | null",
    "parser_version": "string | null"
  },
  "quality_checks": {
    "is_blurry": "boolean | null",
    "is_noisy": "boolean | null",
    "ocr_confidence": "float | null",
    "warnings": "[string] | null"
  }
}
"""
    prompt = f"""
Your task is to act as an advanced invoice parsing engine. Analyze the following raw OCR text and extract, structure, and enrich the data according to the JSON schema provided below.

**Raw OCR Text:**
\"\"\"{text}\"\"\"

**Pre-Processing Checks:**

* Analyze the raw text for indications of poor OCR quality (e.g., gibberish, repeated characters, unusually low confidence scores if available from the OCR process).
* If there are strong indicators of unreadable content, return a JSON object with a "quality_warning" field: {{"quality_warning": "Low OCR confidence due to potential blur/noise/poor scan."}}.

**Extraction and Processing Requirements:**

1.  **Core Field Extraction:**
    * Extract: invoice_number, invoice_date, due_date, currency, po_number, payment_terms.
    * Validate dates to ensure the format MM-DD-YYYY.
    * Flag any discrepancies found (e.g., illogical dates). Include a confidence score for each extracted field.

2.  **Party Details:**
    * **Vendor:** Extract name, address, tax_id, contact (email and/or phone).
    * **Payer:** Extract name, address, billing_reference.
    * Normalize addresses by expanding common abbreviations (e.g., "St" becomes "Street"). Include a confidence score for each extracted field.

3.  **Line Item Processing:**
    * For each line item, extract: description, quantity, unit_price, total, tax_rate (if present), sku (if present), category (infer from description if not explicitly present).
    * Handle multi-line descriptions and potential splitting/merging of items gracefully. Include a confidence score for each extracted field.

4.  **Smart Grouping & Enrichment:**
    * Group the extracted `line_items` by `tax_rate` and `category`.
    * For each group, calculate and include a `subtotal` and an array of the indices of the line items belonging to that group (referencing the `line_items` array).

5.  **Totals Validation:**
    * Extract: subtotal, taxes (breakdown by tax rate if possible), discount, shipping, grand_total.
    * Verify the consistency of these totals based on the extracted line items and tax rates.
    * Recalculate expected totals and include a `validation_warning` field with details if there's a mismatch.

**Output Requirements:**

Return a strictly valid JSON object conforming to the schema below. Use `null` for any missing fields. Ensure all special characters are properly escaped. Include a "confidence_score" (0-100%) for each extracted field where ambiguity exists within the `basic_information` and `party_details` sections. For `line_items`, include a confidence score for each sub-field within each item.

```json
{schema_str}
"""
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        logger.info("Sending request to OpenAI for structured data extraction.")
        response = client.chat.completions.create(
            model="gpt-4o",  # Change to another model as needed
            messages=[
                {"role": "system", "content": "You must output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        logger.info("Successfully received response from OpenAI.")
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        logger.debug(f"Problematic JSON: {response.choices[0].message.content}")
        return {}
    except Exception as e:
        logger.error(f"Error during OpenAI API call: {str(e)}")
        raise


def annotate_image(original_img: np.ndarray, ocr_data: str, save_path: str):
    """Annotate image with OCR bounding boxes and labels and save to disk."""
    try:
        data = pytesseract.image_to_data(original_img, output_type=pytesseract.Output.DICT)
        annotated_img = original_img.copy()

        for i in range(len(data['text'])):
            text = data['text'][i]
            conf = int(data['conf'][i])
            if conf > 60 and text.strip():  # Filter low-confidence or empty results
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                cv2.rectangle(annotated_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(annotated_img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (36, 255, 12), 1)

        cv2.imwrite(save_path, annotated_img)
        logger.info(f"Saved annotated image to {save_path}")
    except Exception as e:
        logger.error(f"Failed to annotate and save image: {str(e)}")


def process_pdf(pdf_path: str) -> dict:
    """Full pipeline: PDF → images → preprocess → OCR → LLM parsing → structured JSON."""
    logger.info(f"Processing PDF: {pdf_path}")
    
    try:
        # Convert PDF to images
        pages = pdf_to_images(pdf_path)
        combined_text = []
        
        # Iterate through all pages
        for page_num, page in enumerate(pages):
            logger.debug(f"Processing page {page_num + 1}/{len(pages)}")
            img_cv = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            proc_img = preprocess_image(img_cv)

            text = ocr_image(proc_img)
            combined_text.append(text)

            annotated_path = f"output/annotated_page_{page_num + 1}.png"
            annotate_image(img_cv, text, annotated_path)

        # Combine text from all pages
        raw_text = "\n".join(combined_text)

        # Log the extracted raw OCR text (caution: could be lengthy)
        logger.debug("--- Extracted OCR Text ---")
        logger.debug(raw_text)
        logger.debug("--- End of OCR Text ---")

        # Extract structured data from raw OCR text
        return extract_structured_data(raw_text)
    except Exception as e:
        logger.error(f"Error during PDF processing: {str(e)}")
        raise