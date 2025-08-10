#!/usr/bin/env python
"""Script to diagnose GCS upload issues."""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.coaching_assistant.utils.gcs_uploader import GCSUploader
from src.coaching_assistant.core.config import settings


def check_gcs_config():
    """Check GCS configuration."""
    print("🔍 Checking GCS Configuration...")
    print("=" * 50)
    
    # Check bucket name
    bucket_name = settings.GOOGLE_STORAGE_BUCKET
    print(f"📦 Bucket Name: {bucket_name or 'NOT SET'}")
    
    # Check if it matches what you expect
    if bucket_name != "coaching-audio-dev":
        print(f"⚠️  WARNING: Bucket name '{bucket_name}' doesn't match 'coaching-audio-dev'")
        print("   This might be why you don't see files with gcloud storage")
    
    # Check credentials
    has_creds = bool(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
    print(f"🔑 Credentials: {'CONFIGURED' if has_creds else 'NOT SET'}")
    
    # Check project ID
    project_id = settings.GOOGLE_PROJECT_ID
    print(f"🏗️  Project ID: {project_id or 'NOT SET'}")
    
    return bucket_name, has_creds


def test_file_listing(bucket_name: str):
    """Test listing files in the bucket."""
    print("\n📋 Testing File Listing...")
    print("=" * 50)
    
    try:
        uploader = GCSUploader(
            bucket_name=bucket_name,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        )
        
        # List all files
        files = uploader.list_files()
        
        if files:
            print(f"✅ Found {len(files)} files in bucket:")
            for f in files[:10]:  # Show first 10
                print(f"   - {f}")
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more")
        else:
            print("⚠️  No files found in bucket")
            print("   Possible reasons:")
            print("   1. Wrong bucket name")
            print("   2. Files uploaded to different bucket")
            print("   3. Permissions issue")
            
        # List audio-uploads specifically
        print("\n📁 Checking audio-uploads/ prefix:")
        audio_files = uploader.list_files(prefix="audio-uploads/")
        
        if audio_files:
            print(f"✅ Found {len(audio_files)} files in audio-uploads/:")
            for f in audio_files[:5]:
                print(f"   - {f}")
        else:
            print("⚠️  No files in audio-uploads/ directory")
            
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []


def test_upload_and_verify():
    """Test uploading a file and verifying it exists."""
    print("\n🧪 Testing Upload and Verification...")
    print("=" * 50)
    
    bucket_name = settings.GOOGLE_STORAGE_BUCKET
    
    try:
        uploader = GCSUploader(
            bucket_name=bucket_name,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        )
        
        # Create a test file
        test_content = b"Test audio file content"
        test_blob_name = "test-uploads/test-file.txt"
        
        print(f"📤 Uploading test file to: {test_blob_name}")
        
        # Upload
        public_url = uploader.upload_file(
            file_content=test_content,
            blob_name=test_blob_name,
            content_type="text/plain"
        )
        
        print(f"✅ Upload successful! Public URL: {public_url}")
        
        # Verify
        exists, size = uploader.check_file_exists(test_blob_name)
        
        if exists:
            print(f"✅ File verified! Size: {size} bytes")
            print(f"\n🎯 You can verify with:")
            print(f"   gcloud storage ls gs://{bucket_name}/test-uploads/")
        else:
            print("❌ File not found after upload!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


def check_signed_url_upload():
    """Check if signed URL upload would work."""
    print("\n🔗 Testing Signed URL Generation...")
    print("=" * 50)
    
    bucket_name = settings.GOOGLE_STORAGE_BUCKET
    
    try:
        uploader = GCSUploader(
            bucket_name=bucket_name,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        )
        
        # Generate signed URL
        test_blob = "audio-uploads/test-user/test-audio.mp3"
        url, expires = uploader.generate_signed_upload_url(
            blob_name=test_blob,
            content_type="audio/mpeg",
            expiration_minutes=60
        )
        
        print(f"✅ Signed URL generated successfully!")
        print(f"   Blob path: {test_blob}")
        print(f"   Expires at: {expires}")
        print(f"\n📝 Expected GCS path: gs://{bucket_name}/{test_blob}")
        print(f"\n💡 To upload a file using this URL, use:")
        print(f"   curl -X PUT -H 'Content-Type: audio/mpeg' \\")
        print(f"        --data-binary @your-file.mp3 \\")
        print(f"        '{url[:80]}...'")
        
    except Exception as e:
        print(f"❌ Failed to generate signed URL: {e}")


def main():
    """Main diagnostic function."""
    print("🚀 GCS Upload Diagnostic Tool")
    print("=" * 70)
    
    # Check configuration
    bucket_name, has_creds = check_gcs_config()
    
    if not bucket_name:
        print("\n❌ GOOGLE_STORAGE_BUCKET not configured!")
        print("   Set it in your .env file:")
        print("   GOOGLE_STORAGE_BUCKET=coaching-audio-dev")
        return
        
    if not has_creds:
        print("\n❌ GOOGLE_APPLICATION_CREDENTIALS_JSON not configured!")
        print("   Add your service account JSON to .env")
        return
    
    # Test file operations
    test_file_listing(bucket_name)
    
    # Test upload
    response = input("\n❓ Do you want to test file upload? (y/n): ")
    if response.lower() == 'y':
        test_upload_and_verify()
    
    # Test signed URL
    check_signed_url_upload()
    
    print("\n" + "=" * 70)
    print("✅ Diagnostic complete!")
    print("\n📌 Summary:")
    print(f"   Configured bucket: {bucket_name}")
    print(f"   Expected bucket: coaching-audio-dev")
    
    if bucket_name != "coaching-audio-dev":
        print(f"\n⚠️  IMPORTANT: Your bucket name doesn't match!")
        print(f"   Either update GOOGLE_STORAGE_BUCKET to 'coaching-audio-dev'")
        print(f"   Or use: gcloud storage ls gs://{bucket_name}/")


if __name__ == "__main__":
    main()