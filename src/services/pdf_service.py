from pdf2image import convert_from_path
from typing import List
from PIL import Image
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Convert each page of a PDF file to a list of PIL Image objects at the specified DPI.

    Args:
        pdf_path (str): Path to the source PDF file.
        dpi (int, optional): Dots per inch for the output images. Defaults to 300.

    Returns:
        List[PIL.Image.Image]: List containing image objects for each PDF page.
    """
    logger.info("Converting PDF to images: '%s' at %d DPI", pdf_path, dpi)
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        logger.info("Successfully converted %d page(s) to images.", len(images))
        return images
    except Exception as e:
        logger.error("Failed to convert PDF '%s' to images: %s", pdf_path, e)
        raise
