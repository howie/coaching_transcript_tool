"""
Google Cloud Storage (GCS) uploader utility.

Provides functionality to interact with GCS for file storage,
such as uploading transcripts or other user-generated content.
"""
import base64
import json
import logging
from google.cloud import storage
from google.oauth2 import service_account
from typing import Optional

from ..core.config import settings

logger = logging.getLogger(__name__)

def get_gcs_client() -> Optional[storage.Client]:
    """
    Initializes and returns a Google Cloud Storage client.

    Uses credentials from the GOOGLE_APPLICATION_CREDENTIALS_JSON
    environment variable.

    Returns:
        An authenticated GCS client instance or None if not configured.
    """
    if not settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
        logger.warning("GCS credentials are not configured. GCS client cannot be created.")
        return None
    
    try:
        # Decode the base64 encoded JSON credentials
        creds_json_str = base64.b64decode(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON).decode('utf-8')
        creds_info = json.loads(creds_json_str)
        
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        client = storage.Client(
            credentials=credentials,
            project=settings.GOOGLE_PROJECT_ID
        )
        logger.info("Successfully created GCS client.")
        return client
    except (base64.binascii.Error, json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to create GCS client from JSON credentials: {e}", exc_info=True)
        return None

def upload_to_gcs(
    file_content: bytes,
    destination_blob_name: str,
    bucket_name: Optional[str] = None,
    content_type: Optional[str] = None
) -> Optional[str]:
    """
    Uploads a file to a GCS bucket.

    Args:
        file_content: The content of the file in bytes.
        destination_blob_name: The name of the object in the GCS bucket.
        bucket_name: The GCS bucket name. Defaults to settings.GOOGLE_STORAGE_BUCKET.
        content_type: The content type of the file (e.g., 'audio/mpeg').

    Returns:
        The public URL of the uploaded file, or None if upload fails.
    """
    gcs_client = get_gcs_client()
    if not gcs_client:
        logger.error("Cannot upload to GCS: client is not available.")
        return None

    target_bucket = bucket_name or settings.GOOGLE_STORAGE_BUCKET
    if not target_bucket:
        logger.error("Cannot upload to GCS: bucket name is not configured.")
        return None

    try:
        bucket = gcs_client.bucket(target_bucket)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(
            file_content,
            content_type=content_type
        )

        logger.info(f"File uploaded to gs://{target_bucket}/{destination_blob_name}")
        return blob.public_url
    except Exception as e:
        logger.error(
            f"Failed to upload to GCS bucket '{target_bucket}': {e}",
            exc_info=True
        )
        return None

# Example usage (for testing purposes)
if __name__ == '__main__':
    # This block will only run when the script is executed directly.
    # You need to have your environment variables set up correctly.
    logging.basicConfig(level=logging.INFO)
    
    # Create a dummy file content
    dummy_content = b"This is a test file for GCS uploader."
    
    # Define destination
    dest_blob = f"test-uploads/test-file-{__import__('datetime').datetime.utcnow().isoformat()}.txt"
    
    # Upload
    public_url = upload_to_gcs(
        file_content=dummy_content,
        destination_blob_name=dest_blob,
        content_type="text/plain"
    )
    
    if public_url:
        print(f"File successfully uploaded. Public URL: {public_url}")
    else:
        print("File upload failed. Check logs for details.")
