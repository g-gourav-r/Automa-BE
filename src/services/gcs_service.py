import os
import logging
import urllib.request
import urllib.parse
import socket
from datetime import datetime, timedelta
from google.cloud import storage
from google.oauth2 import service_account
from google.auth import default
from google.cloud import iam_credentials_v1

from src.core.config import settings

logger = logging.getLogger(__name__)

# Global signer components
iam_client = None
service_account_email = None

# Initialise based on environment
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
    try:
        # Get default credentials
        credentials, project = default()
        storage_client = storage.Client(credentials=credentials)
        logger.info("GCS client initialised with default credentials.")

        # Get service account email from metadata server
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email",
            headers={'Metadata-Flavor': 'Google'}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            service_account_email = response.read().decode('utf-8')
        logger.info("Retrieved service account email: %s", service_account_email)

        # Create IAM client
        iam_client = iam_credentials_v1.IAMCredentialsClient(credentials=credentials)
        logger.info("IAM client initialised.")

    except socket.timeout:
        logger.error("Metadata server request timed out. Are you in a GCP environment?")
        raise
    except Exception as e:
        logger.error("Failed to initialise GCS client: %s", e)
        raise

bucket_name = settings.STORAGE_BUCKET_NAME

def sign_blob(data: bytes) -> bytes:
    """Sign data using IAM Credentials API"""
    request = iam_credentials_v1.SignBlobRequest(
        name=f"projects/-/serviceAccounts/{service_account_email}",
        payload=data,
    )
    response = iam_client.sign_blob(request=request)
    return response.signed_blob

def generate_signed_url(bucket_name: str, blob_path: str, expiration_minutes: int = 15) -> str:
    """Generate a signed URL using IAM-based signing"""
    try:
        expiration = int((datetime.utcnow() + timedelta(minutes=expiration_minutes)).timestamp())
        
        # String to sign
        string_to_sign = (
            "GET\n"
            "\n"  # Content-MD5
            "\n"  # Content-Type
            f"{expiration}\n"
            f"/{bucket_name}/{blob_path}"
        )
        
        # Get signature
        signature = sign_blob(string_to_sign.encode('utf-8'))
        
        # Construct URL
        encoded_signature = urllib.parse.quote(signature)
        url = (
            f"https://storage.googleapis.com/{bucket_name}/{blob_path}"
            f"?GoogleAccessId={service_account_email}"
            f"&Expires={expiration}"
            f"&Signature={encoded_signature}"
        )
        
        logger.info("Signed URL generated for blob: %s", blob_path)
        return url
    except Exception as e:
        logger.error("Failed to generate signed URL for blob %s: %s", blob_path, e)
        raise

def upload_to_gcs(company_id: str, user_id: str, source_file_path: str,
                  destination_blob_name: str, expiration_minutes: int = 15) -> str:
    """Upload a file to GCS and return a signed URL"""
    try:
        blob_path = f"{company_id}/{user_id}/{destination_blob_name}"
        
        # Upload using storage client
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(source_file_path)
        logger.info("File uploaded to: %s", blob_path)

        # Generate signed URL
        url = generate_signed_url(bucket_name, blob_path, expiration_minutes)
        logger.info("Signed URL valid for %d minutes", expiration_minutes)
        return url
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise