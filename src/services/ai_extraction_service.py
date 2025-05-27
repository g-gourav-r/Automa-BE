import openai
import json
import re
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

def extract_key_values_with_ai(text: str, word_positions: list[dict], template_description: str) -> dict:
    """
    Use OpenAI's API to extract key-value pairs from OCR text and word positions based on a given template.

    Args:
        text (str): The OCR-extracted text from the document.
        word_positions (list[dict]): A list of word positions, each containing coordinates.
        template_description (str): A human-readable description of the document structure.

    Returns:
        dict: Extracted key-value pairs with bounding box positions or an error message.
    """
    logger.debug("Extracting key-value pairs via AI...")

    prompt = f"""
        You are an intelligent document extraction AI.
        Given the OCR text and word positions from a scanned document, and a human-provided template description:
        - Infer document fields and extract key-value pairs.
        - Use word positions to determine bounding boxes (combine multi-line values where necessary).
        - For missing or uncertain values, use "N/A".
        - Respond only with valid JSON, no comments or extra text.

        Example Output:
        {{
            "key_values": [
                {{
                    "key": "Invoice Number",
                    "value": "123456",
                    "position": {{ "x": 100, "y": 200, "w": 150, "h": 30 }}
                }}
            ]
        }}

        Template Description:
        {template_description}

        OCR Text:
        {text}

        Word Positions:
        {json.dumps(word_positions, indent=2)}
    """

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a strict JSON-outputting agent. Return only valid JSON with no comments, markdown, or explanations."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content.strip()

        # Remove accidental code block formatting
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        logger.debug("AI response received successfully.")
        logger.debug(f"AI response content: {content}")

        return json.loads(content)

    except Exception as e:
        logger.error("AI extraction failed: %s", e)
        return {"message": "Failed to extract data using AI."}

def extract_key_values_with_ai_for_template(text: str, word_positions: list[dict], template_description: str, template_parsed_data: dict) -> dict:
    """
    Use OpenAI's API to extract key-value pairs from OCR text and word positions based on a given template and parsed fields.

    Args:
        text (str): The OCR-extracted text from the document.
        word_positions (list[dict]): A list of word positions, each containing coordinates.
        template_description (str): A human-readable description of the document structure.
        template_parsed_data (dict): The fields you need to extract.

    Returns:
        dict: Extracted key-value pairs with bounding box positions or an error message.
    """
    logger.debug("Extracting key-value pairs via AI for a specific template...")

    prompt = f"""
        You are an intelligent document extraction AI.

        Your task is to extract specific key-value pairs from a scanned document, based on:
        - OCR text content,
        - word positions with their bounding boxes,
        - a human-provided template description,
        - and a list of expected fields.

        **Extraction instructions:**
        - Only extract the fields listed in the expected fields.
        - Use the template description and the document text context to determine the most appropriate value for each field.
        - If a value cannot be confidently determined from the text, set its value to "N/A" and its position to null.
        - Use word positions to determine the bounding box for each extracted value.
        - If a value spans multiple words or lines, combine their bounding boxes into one.
        - Do not infer values not clearly indicated by the document text.
        - Do not guess. If unsure, mark as "N/A".
        - Respond with valid, minified JSON — no markdown, no comments, no explanations.

        **Example JSON response:**
        {{
        "key_values": [
            {{
            "key": "Invoice Number",
            "value": "123456",
            "position": {{ "x": 100, "y": 200, "w": 150, "h": 30 }}
            }},
            {{
            "key": "Customer Name",
            "value": "N/A",
            "position": null
            }}
        ]
        }}

        **Template Description:**
        {template_description}

        **Expected Fields:**
        {json.dumps(list(template_parsed_data.keys()), indent=2)}

        **OCR Text:**
        {text}

        **Word Positions:**
        {json.dumps(word_positions, indent=2)}
        """

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a strict JSON-outputting agent. Return only valid JSON with no comments, markdown, or explanations."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content.strip()

        # Remove accidental code block formatting
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        logger.debug("AI response received successfully.")
        logger.debug(f"AI response content: {content}")

        return json.loads(content)

    except Exception as e:
        logger.error("AI extraction failed: %s", e)
        return {"message": "Failed to extract data using AI."}
