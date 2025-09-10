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
from typing import Optional, Tuple
from datetime import datetime, timedelta

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
        logger.warning(
            "GCS credentials are not configured. GCS client cannot be created."
        )
        return None

    try:
        # Decode the base64 encoded JSON credentials
        creds_json_str = base64.b64decode(
            settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        ).decode("utf-8")
        creds_info = json.loads(creds_json_str)

        credentials = service_account.Credentials.from_service_account_info(
            creds_info
        )
        client = storage.Client(
            credentials=credentials, project=settings.GOOGLE_PROJECT_ID
        )
        logger.info("Successfully created GCS client.")
        return client
    except (base64.binascii.Error, json.JSONDecodeError, Exception) as e:
        logger.error(
            f"Failed to create GCS client from JSON credentials: {e}",
            exc_info=True,
        )
        return None


def upload_to_gcs(
    file_content: bytes,
    destination_blob_name: str,
    bucket_name: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Optional[str]:
    """
    Uploads a file to a GCS bucket.

    Args:
        file_content: The content of the file in bytes.
        destination_blob_name: The name of the object in the GCS bucket.
        bucket_name: The GCS bucket name. Defaults to settings.AUDIO_STORAGE_BUCKET.
        content_type: The content type of the file (e.g., 'audio/mpeg').

    Returns:
        The public URL of the uploaded file, or None if upload fails.
    """
    gcs_client = get_gcs_client()
    if not gcs_client:
        logger.error("Cannot upload to GCS: client is not available.")
        return None

    target_bucket = bucket_name or settings.AUDIO_STORAGE_BUCKET
    if not target_bucket:
        logger.error("Cannot upload to GCS: bucket name is not configured.")
        return None

    try:
        bucket = gcs_client.bucket(target_bucket)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(file_content, content_type=content_type)

        logger.info(
            f"File uploaded to gs://{target_bucket}/{destination_blob_name}"
        )
        return blob.public_url
    except Exception as e:
        logger.error(
            f"Failed to upload to GCS bucket '{target_bucket}': {e}",
            exc_info=True,
        )
        return None


class GCSUploader:
    """Google Cloud Storage uploader with signed URL support."""

    def __init__(self, bucket_name: str, credentials_json: str = None):
        """
        Initialize GCS uploader.

        Args:
            bucket_name: GCS bucket name
            credentials_json: JSON credentials string (optional)
        """
        self.bucket_name = bucket_name
        self.credentials_json = (
            credentials_json or settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        )
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize GCS client."""
        if not self.credentials_json:
            logger.warning("GCS credentials not provided")
            return

        try:
            # Try to parse as JSON directly first
            try:
                creds_info = json.loads(self.credentials_json)
            except json.JSONDecodeError:
                # If that fails, try base64 decoding first
                creds_json_str = base64.b64decode(
                    self.credentials_json
                ).decode("utf-8")
                creds_info = json.loads(creds_json_str)

            credentials = (
                service_account.Credentials.from_service_account_info(
                    creds_info
                )
            )
            self.client = storage.Client(
                credentials=credentials, project=settings.GOOGLE_PROJECT_ID
            )
            logger.info("GCSUploader initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.client = None

    def generate_signed_upload_url(
        self,
        blob_name: str,
        content_type: str = "application/octet-stream",
        expiration_minutes: int = 60,
    ) -> Tuple[str, datetime]:
        """
        Generate a signed URL for uploading files to GCS.

        Args:
            blob_name: Name of the blob in GCS
            content_type: Content type of the file
            expiration_minutes: URL expiration time in minutes

        Returns:
            Tuple of (signed_url, expiration_datetime)
        """
        if not self.client:
            logger.error(
                "❌ GCS client not initialized - cannot generate signed URL"
            )
            raise ValueError("GCS client not initialized")

        logger.info(f"🔗 Generating signed URL for upload...")
        logger.info(f"🪣 Bucket: {self.bucket_name}")
        logger.info(f"📄 Blob: {blob_name}")
        logger.info(f"🏷️  Content-Type: {content_type}")
        logger.info(f"⏱️  Expiration: {expiration_minutes} minutes")

        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)

            expiration = datetime.utcnow() + timedelta(
                minutes=expiration_minutes
            )

            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="PUT",
                content_type=content_type,
            )

            logger.info(f"✅ Signed URL generated successfully")
            logger.info(f"🔗 URL (partial): {url[:50]}...{url[-10:]}")
            logger.info(f"⏰ Expires at: {expiration}")

            return url, expiration

        except Exception as e:
            logger.error(f"❌ Failed to generate signed URL: {e}")
            raise

    def generate_signed_read_url(
        self, blob_name: str, expiration_minutes: int = 60
    ) -> str:
        """
        Generate a signed URL for reading/downloading files from GCS.

        Args:
            blob_name: Name of the blob in GCS
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL for reading the file
        """
        if not self.client:
            logger.error(
                "❌ GCS client not initialized - cannot generate signed read URL"
            )
            raise ValueError("GCS client not initialized")

        logger.info(f"🔗 Generating signed READ URL...")
        logger.info(f"🪣 Bucket: {self.bucket_name}")
        logger.info(f"📄 Blob: {blob_name}")
        logger.info(f"⏱️  Expiration: {expiration_minutes} minutes")

        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)

            expiration = datetime.utcnow() + timedelta(
                minutes=expiration_minutes
            )

            url = blob.generate_signed_url(
                version="v4", expiration=expiration, method="GET"
            )

            logger.info(f"✅ Signed READ URL generated successfully")
            logger.info(f"🔗 URL (partial): {url[:50]}...{url[-10:]}")

            return url

        except Exception as e:
            logger.error(f"❌ Failed to generate signed read URL: {e}")
            raise

    def upload_file(
        self,
        file_content: bytes,
        blob_name: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload file directly to GCS.

        Args:
            file_content: File content as bytes
            blob_name: Name of the blob in GCS
            content_type: Content type of the file

        Returns:
            Public URL of the uploaded file
        """
        if not self.client:
            raise ValueError("GCS client not initialized")

        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)

        blob.upload_from_string(file_content, content_type=content_type)

        return blob.public_url

    def check_file_exists(self, blob_name: str) -> Tuple[bool, Optional[int]]:
        """
        Check if a file exists in GCS and get its size.

        Args:
            blob_name: Name of the blob in GCS

        Returns:
            Tuple of (exists, file_size_in_bytes)
        """
        if not self.client:
            logger.warning("GCS client not initialized, cannot check file")
            return False, None

        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)

            # This will make a HEAD request to check if blob exists
            if blob.exists():
                # Reload to get metadata including size
                blob.reload()
                return True, blob.size
            else:
                return False, None

        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False, None

    def list_files(self, prefix: str = None) -> list:
        """
        List files in the bucket with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of blob names
        """
        if not self.client:
            logger.warning("GCS client not initialized")
            return []

        try:
            bucket = self.client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []


# Example usage (for testing purposes)
if __name__ == "__main__":
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
        content_type="text/plain",
    )

    if public_url:
        print(f"File successfully uploaded. Public URL: {public_url}")
    else:
        print("File upload failed. Check logs for details.")
