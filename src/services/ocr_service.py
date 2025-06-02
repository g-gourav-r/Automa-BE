import numpy as np
import logging
import pytesseract
import cv2

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Convert an image to greyscale and apply Otsu's thresholding 
    to enhance text clarity for OCR.

    Args:
        image (np.ndarray): Input image in BGR format.

    Returns:
        np.ndarray: Preprocessed binary image ready for OCR.
    """
    logger.debug("Starting image preprocessing for OCR.")
    try:
        # Convert image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Otsu's thresholding to binarise the image
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        logger.debug("Image preprocessing completed.")
        return thresh

    except Exception as e:
        logger.error("Error preprocessing image: %s", e)
        raise


def ocr_image(image: np.ndarray) -> str:
    """
    Extract text from a preprocessed image using Tesseract OCR.

    Args:
        image (np.ndarray): Preprocessed (binary) image.

    Returns:
        str: Recognised text extracted by Tesseract.
    """
    logger.debug("Performing OCR on the image.")
    try:
        # Run OCR and extract text
        text = pytesseract.image_to_string(image)
        logger.debug("OCR extraction completed.")
        return text

    except Exception as e:
        logger.error("Error during OCR process: %s", e)
        raise


def extract_word_positions(image: np.ndarray) -> list[dict]:
    """
    Extract word positions (bounding boxes) from an image using Tesseract OCR.

    Args:
        image (np.ndarray): Original image in BGR format.

    Returns:
        list[dict]: A list of dictionaries containing recognised words and 
                    their corresponding bounding box positions:
                    {
                        'text': word string,
                        'x': top-left X coordinate,
                        'y': top-left Y coordinate,
                        'w': width of the bounding box,
                        'h': height of the bounding box
                    }
    """
    logger.debug("Extracting word positions from image using Tesseract.")
    try:
        # Use pytesseract to get detailed OCR data, including positions and confidence scores
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # Extract word positions where confidence is greater than zero and text is not empty
        positions = [
            {
                "text": data['text'][i],
                "x": data['left'][i],
                "y": data['top'][i],
                "w": data['width'][i],
                "h": data['height'][i]
            }
            for i in range(len(data['text']))
            if int(data['conf'][i]) > 0 and data['text'][i].strip()
        ]

        logger.info("Extracted %d word positions.", len(positions))
        return positions

    except Exception as e:
        logger.error("Word position extraction failed: %s", e)
        raise
