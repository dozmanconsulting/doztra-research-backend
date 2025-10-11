#!/usr/bin/env python3
"""
Test script to verify GCS connection and bucket access.
"""
import os
import sys
import logging
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gcs_connection():
    """Test connection to Google Cloud Storage."""
    try:
        # Check if credentials are set
        if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return False
        
        # Check if credentials file exists
        creds_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        if not os.path.exists(creds_path):
            logger.error(f"Credentials file not found: {creds_path}")
            return False
        
        logger.info(f"Using credentials from: {creds_path}")
        
        # Initialize GCS client
        client = storage.Client()
        logger.info(f"Successfully initialized GCS client: {client.project}")
        
        # Get bucket name from environment or argument
        bucket_name = os.environ.get("GCS_BUCKET_NAME")
        if not bucket_name and len(sys.argv) > 1:
            bucket_name = sys.argv[1]
        
        if not bucket_name:
            logger.error("No bucket name provided. Set GCS_BUCKET_NAME or provide as argument")
            return False
        
        # Try to access bucket
        try:
            bucket = client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(max_results=5))
            
            logger.info(f"Successfully connected to bucket: {bucket_name}")
            logger.info(f"Found {len(blobs)} objects in bucket")
            
            # List a few objects if any
            if blobs:
                logger.info("Sample objects:")
                for blob in blobs:
                    logger.info(f"  - {blob.name} ({blob.size} bytes)")
            
            # Try to create a test file
            test_blob = bucket.blob("test_connection.txt")
            test_blob.upload_from_string("GCS connection test successful")
            logger.info("Successfully uploaded test file")
            
            # Delete test file
            test_blob.delete()
            logger.info("Successfully deleted test file")
            
            return True
        except GoogleCloudError as e:
            logger.error(f"Failed to access bucket {bucket_name}: {str(e)}")
            return False
    
    except Exception as e:
        logger.error(f"Error testing GCS connection: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing GCS connection...")
    success = test_gcs_connection()
    
    if success:
        logger.info("✅ GCS connection test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ GCS connection test FAILED")
        sys.exit(1)
