"""
Google Cloud Storage service for handling file uploads and downloads.
"""
import os
import shutil
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from typing import Optional, Dict, Any
from app.core.config import settings

# Try to import Google Cloud Storage client
try:
    from google.cloud import storage
    from google.cloud.exceptions import GoogleCloudError
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

class GCSStorageService:
    def __init__(self):
        # Set up local storage paths for fallback
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Set up GCS client if available and configured
        self.gcs_client = None
        self.use_gcs = settings.USE_GCS_STORAGE if hasattr(settings, 'USE_GCS_STORAGE') else False
        
        if self.use_gcs and GCS_AVAILABLE:
            # Initialize GCS client
            self.gcs_client = storage.Client()
            self.bucket_name = settings.GCS_BUCKET_NAME
            self.bucket = self.gcs_client.bucket(self.bucket_name)
    
    async def upload_file(self, file: UploadFile, user_id: str, document_id: str) -> Dict[str, Any]:
        """
        Upload a file to Google Cloud Storage and return file metadata.
        
        Args:
            file: The uploaded file
            user_id: User ID
            document_id: Document ID
            
        Returns:
            Dict with file metadata including path, size, etc.
        """
        # Create file path
        file_name = file.filename
        
        if self.use_gcs and self.gcs_client:
            # Upload to GCS
            try:
                # Create blob path
                blob_path = f"{user_id}/{document_id}/{file_name}"
                
                # Get blob
                blob = self.bucket.blob(blob_path)
                
                # Read file content into memory
                content = await file.read()
                
                # Upload to GCS
                blob.upload_from_string(content, content_type=file.content_type)
                
                # Return file metadata
                return {
                    "file_path": f"gs://{self.bucket_name}/{blob_path}",
                    "file_size": blob.size,
                    "storage_type": "gcs"
                }
            except GoogleCloudError as e:
                raise Exception(f"GCS upload error: {str(e)}")
        else:
            # Upload to local file system as fallback
            try:
                # Create user directory if it doesn't exist
                user_dir = self.upload_dir / str(user_id)
                user_dir.mkdir(exist_ok=True)
                
                # Create document directory
                doc_dir = user_dir / document_id
                doc_dir.mkdir(exist_ok=True)
                
                # Save file path
                file_path = doc_dir / file_name
                
                # Save file using async I/O
                async with aiofiles.open(file_path, "wb") as buffer:
                    # Read file content into memory first to avoid blocking I/O
                    content = await file.read()
                    await buffer.write(content)
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Return file metadata
                return {
                    "file_path": str(file_path),
                    "file_size": file_size,
                    "storage_type": "local"
                }
            except Exception as e:
                raise Exception(f"Local file upload error: {str(e)}")
    
    async def download_file(self, file_path: str, local_path: Optional[str] = None) -> str:
        """
        Download a file from storage to local path.
        
        Args:
            file_path: Path to the file in storage
            local_path: Local path to save the file (optional)
            
        Returns:
            Path to the downloaded file
        """
        # Check if file is in GCS
        if file_path.startswith("gs://") and self.gcs_client:
            try:
                # Extract bucket and blob path from GCS URI
                parts = file_path.replace("gs://", "").split("/")
                bucket_name = parts[0]
                blob_path = "/".join(parts[1:])
                
                # Create local path if not provided
                if not local_path:
                    local_path = f"/tmp/{os.path.basename(blob_path)}"
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Get bucket and blob
                bucket = self.gcs_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                
                # Download file
                blob.download_to_filename(local_path)
                
                return local_path
            except GoogleCloudError as e:
                raise Exception(f"GCS download error: {str(e)}")
        else:
            # File is in local storage
            if not local_path:
                return file_path  # File is already local
            
            try:
                # Copy file to new location
                shutil.copy(file_path, local_path)
                return local_path
            except Exception as e:
                raise Exception(f"Local file download error: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            True if deletion was successful
        """
        # Check if file is in GCS
        if file_path.startswith("gs://") and self.gcs_client:
            try:
                # Extract bucket and blob path from GCS URI
                parts = file_path.replace("gs://", "").split("/")
                bucket_name = parts[0]
                blob_path = "/".join(parts[1:])
                
                # Get bucket and blob
                bucket = self.gcs_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                
                # Delete blob
                blob.delete()
                
                return True
            except GoogleCloudError as e:
                raise Exception(f"GCS delete error: {str(e)}")
        else:
            # File is in local storage
            try:
                # Delete file
                os.remove(file_path)
                
                # Check if parent directory is empty and delete if it is
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                
                return True
            except Exception as e:
                raise Exception(f"Local file delete error: {str(e)}")
