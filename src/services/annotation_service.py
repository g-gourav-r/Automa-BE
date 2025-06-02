import os
import cv2
import numpy as np
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def annotate_from_ai_response(image: np.ndarray, ai_response: Dict[str, Any], output_path: str) -> None:
    """
    Annotate an image with bounding boxes and labels based on AI response data.

    Args:
        image (np.ndarray): The input image as a NumPy array.
        ai_response (dict): Dictionary containing AI-detected key-value data and positions.
        output_path (str): Path to save the annotated image.
    """
    try:
        annotated_image = image.copy()
        key_values = ai_response.get("key_values", [])

        if not key_values:
            logger.warning("No 'key_values' found in AI response.")
            return

        for item in key_values:
            key = item.get("key")
            position = item.get("position")

            if not key or not position:
                logger.warning("Incomplete key-value pair encountered: %s", item)
                continue

            x, y, w, h = position.get("x"), position.get("y"), position.get("w"), position.get("h")
            if None in (x, y, w, h):
                logger.warning("Incomplete position data for key '%s': %s", key, position)
                continue

            # Draw rectangle and label
            cv2.rectangle(annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            font_scale = 0.5
            thickness = 1
            (text_w, text_h), _ = cv2.getTextSize(key, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_x, text_y = x, y - 5 if y - 5 > 10 else y + text_h + 5

            cv2.rectangle(annotated_image, (text_x - 2, text_y - text_h - 2),
                          (text_x + text_w + 2, text_y + 2), (0, 255, 0), -1)
            cv2.putText(annotated_image, key, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, annotated_image)
        logger.info("Annotated image saved at: %s", output_path)

    except Exception as e:
        logger.error("Failed to annotate image from AI response: %s", e)
        raise
