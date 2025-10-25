"""
Storage service for handling file uploads and downloads.
Supports local file system, AWS S3, and Google Cloud Storage.
"""
import os
import shutil
import aiofiles
import logging
from pathlib import Path
from fastapi import UploadFile
from typing import Optional, Dict, Any
from app.core.config import settings
from datetime import timedelta

# Configure logger
logger = logging.getLogger(__name__)

# Try to import boto3 for S3 support
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

# Try to import Google Cloud Storage client
try:
    from google.cloud import storage
    from google.cloud.exceptions import GoogleCloudError
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

class StorageService:
    def __init__(self):
        # Set up local storage paths
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Set up S3 client if available and configured
        self.s3_client = None
        self.use_s3 = settings.USE_S3_STORAGE if hasattr(settings, 'USE_S3_STORAGE') else False
        
        if self.use_s3 and S3_AVAILABLE:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.AWS_BUCKET_NAME
        
        # Set up GCS client variables (will initialize lazily)
        self.gcs_client = None
        self.bucket = None
        self.gcs_bucket_name = None
        
        # Check environment variables first, then settings
        self.use_gcs = os.environ.get('USE_GCS_STORAGE', '').lower() == 'true'
        if not self.use_gcs and hasattr(settings, 'USE_GCS_STORAGE'):
            self.use_gcs = settings.USE_GCS_STORAGE
        
        # Get bucket name from environment or settings
        if self.use_gcs:
            self.gcs_bucket_name = os.environ.get('GCS_BUCKET_NAME')
            if not self.gcs_bucket_name and hasattr(settings, 'GCS_BUCKET_NAME'):
                self.gcs_bucket_name = settings.GCS_BUCKET_NAME
            
            if not self.gcs_bucket_name:
                logger.warning("GCS_BUCKET_NAME not configured, disabling GCS storage")
                self.use_gcs = False
    
    def _init_gcs_client(self):
        """Initialize GCS client lazily when needed"""
        if self.use_gcs and GCS_AVAILABLE and not self.gcs_client:
            try:
                # Initialize GCS client
                self.gcs_client = storage.Client()
                
                if not self.gcs_bucket_name:
                    raise ValueError("GCS_BUCKET_NAME not configured")
                    
                # Get bucket
                self.bucket = self.gcs_client.bucket(self.gcs_bucket_name)
                
                logger.info(f"GCS storage initialized with bucket: {self.gcs_bucket_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {str(e)}")
                self.use_gcs = False
                return False
        return self.use_gcs and self.gcs_client and self.bucket
    
    async def upload_file(self, file: UploadFile, user_id: str, document_id: str) -> Dict[str, Any]:
        """
        Upload a file to storage and return file metadata.
        
        Args:
            file: The uploaded file
            user_id: User ID
            document_id: Document ID
            
        Returns:
            Dict with file metadata including path, size, etc.
        """
        # Create file path
        file_name = file.filename
        
        # Check if GCS is configured (preferred over S3)
        if self.use_gcs and self._init_gcs_client():
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
                    "file_path": f"gs://{self.gcs_bucket_name}/{blob_path}",
                    "file_size": blob.size,
                    "storage_type": "gcs"
                }
            except GoogleCloudError as e:
                raise Exception(f"GCS upload error: {str(e)}")
        elif self.use_s3 and self.s3_client:
            # Upload to S3
            try:
                file_key = f"{user_id}/{document_id}/{file_name}"
                
                # Upload file
                self.s3_client.upload_fileobj(
                    file.file,
                    self.bucket_name,
                    file_key
                )
                
                # Get file size
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
                file_size = response['ContentLength']
                
                # Return file metadata
                return {
                    "file_path": f"s3://{self.bucket_name}/{file_key}",
                    "file_size": file_size,
                    "storage_type": "s3"
                }
            except ClientError as e:
                raise Exception(f"S3 upload error: {str(e)}")
        else:
            # Upload to local file system
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
        if file_path.startswith("gs://") and self._init_gcs_client():
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
        # Check if file is in S3
        elif file_path.startswith("s3://") and self.s3_client:
            try:
                # Extract bucket and key from S3 URI
                parts = file_path.replace("s3://", "").split("/")
                bucket = parts[0]
                key = "/".join(parts[1:])
                
                # Create local path if not provided
                if not local_path:
                    local_path = f"/tmp/{os.path.basename(key)}"
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Download file
                self.s3_client.download_file(bucket, key, local_path)
                
                return local_path
            except ClientError as e:
                raise Exception(f"S3 download error: {str(e)}")
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
        if file_path.startswith("gs://") and self._init_gcs_client():
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
        # Check if file is in S3
        elif file_path.startswith("s3://") and self.s3_client:
            try:
                # Extract bucket and key from S3 URI
                parts = file_path.replace("s3://", "").split("/")
                bucket = parts[0]
                key = "/".join(parts[1:])
                
                # Delete file
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                
                return True
            except ClientError as e:
                raise Exception(f"S3 delete error: {str(e)}")
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

    def generate_signed_url(self, file_path: str, expires_seconds: int = 3600) -> Optional[str]:
        """Generate a temporary signed HTTPS URL for a stored file if remote storage is used."""
        try:
            if file_path.startswith("gs://"):
                if not self._init_gcs_client():
                    return None
                parts = file_path.replace("gs://", "").split("/")
                bucket_name = parts[0]
                blob_path = "/".join(parts[1:])
                bucket = self.gcs_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                url = blob.generate_signed_url(expiration=timedelta(seconds=expires_seconds), method="GET", version="v4")
                return url
            if file_path.startswith("s3://") and self.s3_client:
                parts = file_path.replace("s3://", "").split("/")
                bucket = parts[0]
                key = "/".join(parts[1:])
                url = self.s3_client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=expires_seconds,
                )
                return url
            if file_path.startswith("http://") or file_path.startswith("https://"):
                return file_path
            return None
        except Exception:
            return None
