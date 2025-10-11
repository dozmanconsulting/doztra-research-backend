"""
Initialize Google Cloud Storage credentials from environment variables.
This module handles the creation of a temporary credentials file when running on Render.com.
"""
import os
import json
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def initialize_gcs_credentials():
    """
    Initialize Google Cloud Storage credentials.
    
    If running on Render.com and GOOGLE_APPLICATION_CREDENTIALS_JSON is set,
    create a temporary file with the credentials.
    """
    # Check if running on Render and credentials JSON is provided
    if "RENDER" in os.environ and "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        try:
            # Create a temporary file
            fd, path = tempfile.mkstemp(suffix='.json')
            with os.fdopen(fd, 'w') as tmp:
                # Write the contents of the environment variable to the file
                tmp.write(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
            
            # Set the environment variable to point to the temporary file
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
            logger.info(f"Created temporary service account key file at {path}")
            
            return path
        except Exception as e:
            logger.error(f"Failed to create temporary credentials file: {str(e)}")
            return None
    
    # Check if credentials file path is provided directly
    elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        creds_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        if os.path.exists(creds_path):
            logger.info(f"Using service account key file at {creds_path}")
            return creds_path
        else:
            logger.warning(f"Specified credentials file does not exist: {creds_path}")
            return None
    
    # Check for credentials in default locations
    else:
        # Check common locations for credentials
        possible_paths = [
            Path.home() / ".config/gcloud/application_default_credentials.json",
            Path("doztra-prod-878acd25b350.json"),  # Current directory
            Path("/app/doztra-prod-878acd25b350.json"),  # Render.com app directory
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found credentials at {path}")
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)
                return str(path)
        
        logger.warning("No GCS credentials found")
        return None
