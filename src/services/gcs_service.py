import os
import logging
from datetime import timedelta
from google.cloud import storage
from google.oauth2 import service_account

from src.core.config import settings

logger = logging.getLogger(__name__)

# Initialise Google Cloud Storage client based on environment
if settings.ENV == "local" and settings.GOOGLE_APPLICATION_CREDENTIALS:
    try:
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        )
        storage_client = storage.Client(credentials=credentials)
        logger.info("GCS client initialised with local service account credentials.")
    except Exception as e:
        logger.error(
            "Failed to load service account credentials from %s: %s. Falling back to default credentials.",
            settings.GOOGLE_APPLICATION_CREDENTIALS,
            e
        )
        storage_client = storage.Client()
else:
    storage_client = storage.Client()
    logger.info("GCS client initialised using default credentials.")

bucket_name = settings.STORAGE_BUCKET_NAME


def generate_signed_url(bucket_name: str, blob_path: str, expiration_minutes: int = 15) -> str:
    """Generate a signed URL for a blob in the specified GCS bucket."""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        url = blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))
        logger.info("Signed URL generated for blob: %s", blob_path)
        return url
    except Exception as e:
        logger.error("Failed to generate signed URL for blob %s: %s", blob_path, e)
        raise


def upload_to_gcs(company_id: str, user_id: str, source_file_path: str,
                  destination_blob_name: str, expiration_minutes: int = 15) -> str:
    """Upload a local file to GCS and return a signed URL."""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob_path = f"{company_id}/{user_id}/{destination_blob_name}"
        blob = bucket.blob(blob_path)

        blob.upload_from_filename(source_file_path)
        logger.info("File '%s' uploaded to '%s'.", source_file_path, blob_path)

        url = blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))
        logger.info("Signed URL (valid for %d minutes): %s", expiration_minutes, url)
        return url
    except Exception as e:
        logger.error("Failed to upload file '%s' to '%s': %s", source_file_path, blob_path, e)
        raise
