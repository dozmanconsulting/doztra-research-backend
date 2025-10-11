#!/usr/bin/env python3
"""
Script to verify GCS setup on Render.com
"""
import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_gcs_setup():
    """Verify GCS setup on Render.com"""
    logger.info("Verifying GCS setup...")
    
    # Check if running on Render
    if "RENDER" in os.environ:
        logger.info("Running on Render.com")
    else:
        logger.info("Not running on Render.com")
    
    # Check if GCS is enabled
    use_gcs = os.environ.get("USE_GCS_STORAGE", "").lower() == "true"
    logger.info(f"GCS storage enabled: {use_gcs}")
    
    # Check if credentials are set
    if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        creds_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        logger.info(f"GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
        
        # Check if file exists
        if os.path.exists(creds_path):
            logger.info(f"Credentials file exists: {creds_path}")
            
            # Check file permissions
            try:
                import stat
                file_stat = os.stat(creds_path)
                permissions = oct(file_stat.st_mode & 0o777)
                logger.info(f"File permissions: {permissions}")
            except Exception as e:
                logger.error(f"Failed to check file permissions: {str(e)}")
        else:
            logger.error(f"Credentials file does not exist: {creds_path}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set")
    
    # Check if JSON credentials are set
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        logger.info("GOOGLE_APPLICATION_CREDENTIALS_JSON is set")
        
        # Try to parse JSON
        try:
            creds_json = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
            logger.info(f"Project ID: {creds_json.get('project_id')}")
            logger.info(f"Client email: {creds_json.get('client_email')}")
        except Exception as e:
            logger.error(f"Failed to parse credentials JSON: {str(e)}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
    
    # Check if bucket name is set
    if "GCS_BUCKET_NAME" in os.environ:
        logger.info(f"GCS_BUCKET_NAME: {os.environ['GCS_BUCKET_NAME']}")
    else:
        logger.warning("GCS_BUCKET_NAME not set")
    
    # Try to import google.cloud.storage
    try:
        from google.cloud import storage
        logger.info("google-cloud-storage package is installed")
        
        # Try to create client
        try:
            client = storage.Client()
            logger.info(f"Successfully created GCS client for project: {client.project}")
            
            # Try to access bucket
            if "GCS_BUCKET_NAME" in os.environ:
                bucket_name = os.environ["GCS_BUCKET_NAME"]
                try:
                    bucket = client.bucket(bucket_name)
                    logger.info(f"Successfully accessed bucket: {bucket_name}")
                    
                    # Try to list blobs
                    try:
                        blobs = list(bucket.list_blobs(max_results=5))
                        logger.info(f"Found {len(blobs)} objects in bucket")
                        
                        # List a few objects if any
                        if blobs:
                            logger.info("Sample objects:")
                            for blob in blobs:
                                logger.info(f"  - {blob.name} ({blob.size} bytes)")
                    except Exception as e:
                        logger.error(f"Failed to list blobs: {str(e)}")
                    
                    # Try to create a test file
                    try:
                        test_blob = bucket.blob("test_connection.txt")
                        test_blob.upload_from_string("GCS connection test successful")
                        logger.info("Successfully uploaded test file")
                        
                        # Delete test file
                        test_blob.delete()
                        logger.info("Successfully deleted test file")
                    except Exception as e:
                        logger.error(f"Failed to create/delete test file: {str(e)}")
                except Exception as e:
                    logger.error(f"Failed to access bucket: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create GCS client: {str(e)}")
    except ImportError:
        logger.error("google-cloud-storage package is not installed")

if __name__ == "__main__":
    verify_gcs_setup()
