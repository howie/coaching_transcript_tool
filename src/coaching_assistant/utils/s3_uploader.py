"""
Utility for uploading files to AWS S3.
"""
import logging
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get S3 configuration from environment variables
S3_BUCKET = os.getenv('S3_BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-1')  # Default to a region if not set

def upload_snippet_to_s3(content: bytes, original_filename: str) -> None:
    """
    Uploads a snippet of a file to an S3 bucket for later review.

    Args:
        content: The byte content of the file.
        original_filename: The original name of the uploaded file.
    """
    if not all([S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        logger.warning(
            'S3 environment variables (S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are not fully configured. ' 
            'Skipping upload of unrecognized format snippet.'
        )
        return

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

        # Take the first 1KB as a snippet
        snippet = content[:1024]

        # Create a unique filename for the snippet
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        s3_key = f"unrecognized_formats/{timestamp}_{original_filename}.txt"

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=snippet,
            ContentType='text/plain'
        )
        logger.info(f"Successfully uploaded snippet to S3: s3://{S3_BUCKET}/{s3_key}")

    except (NoCredentialsError, PartialCredentialsError):
        logger.error("AWS credentials not found. Please configure them in your environment.")
    except ClientError as e:
        logger.error(f"An S3 client error occurred: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during S3 upload: {e}")
