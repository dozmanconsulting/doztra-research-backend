"""
Document service for handling document operations.
"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, BackgroundTasks
from datetime import datetime

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.storage_service import StorageService
from app.services.openai_service import process_document as openai_process_document
from app.core.config import settings

# Semaphore to limit concurrent processing tasks
processing_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_PROCESSING if hasattr(settings, 'MAX_CONCURRENT_PROCESSING') else 3)

class DocumentService:
    def __init__(self):
        self.storage_service = StorageService()
    
    async def upload_document(
        self,
        db: Session,
        file: UploadFile,
        user_id: str,
        document_id: str,
        background_tasks: BackgroundTasks,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Upload a document and schedule processing.
        
        Args:
            db: Database session
            file: Uploaded file
            user_id: User ID
            document_id: Document ID
            background_tasks: FastAPI background tasks
            metadata: Optional metadata
            
        Returns:
            Document object
        """
        try:
            # Upload file to storage
            file_info = await self.storage_service.upload_file(file, user_id, document_id)
            
            # Create document record
            document = Document(
                id=document_id,
                user_id=user_id,
                title=metadata.get("title") if metadata else None,
                original_filename=file.filename,
                file_path=file_info["file_path"],
                file_type=file.content_type,
                file_size=file_info["file_size"],
                upload_date=datetime.utcnow(),
                processing_status="pending",
                metadata=metadata or {}
            )
            
            # Add to database
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Schedule background processing
            background_tasks.add_task(
                self.process_document_background,
                document_id=document_id,
                user_id=user_id,
                file_path=file_info["file_path"],
                file_type=file.content_type,
                metadata=metadata or {}
            )
            
            return document
        except Exception as e:
            db.rollback()
            raise e
    
    async def process_document_background(
        self,
        document_id: str,
        user_id: str,
        file_path: str,
        file_type: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Process document in the background with concurrency control.
        
        Args:
            document_id: Document ID
            user_id: User ID
            file_path: Path to the file
            file_type: File content type
            metadata: Document metadata
        """
        # Get database session
        from app.db.session import SessionLocal
        db = SessionLocal()
        
        try:
            # Update document status to processing
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            document.processing_status = "processing"
            db.commit()
            
            # Acquire semaphore to limit concurrent processing
            async with processing_semaphore:
                try:
                    # Download file if it's in cloud storage
                    local_file_path = await self.storage_service.download_file(file_path)
                    
                    # Process document with optimized settings
                    # Determine optimal chunk size based on document length
                    document_size = document.file_size
                    chunk_size = self._get_optimal_chunk_size(document_size)
                    
                    # Process document
                    chunks = await openai_process_document(
                        file_path=local_file_path,
                        file_type=file_type,
                        document_id=document_id,
                        user_id=user_id,
                        metadata=metadata,
                        chunk_size=chunk_size
                    )
                    
                    # Save chunks to database
                    await self._save_chunks_to_db(db, document_id, chunks)
                    
                    # Update document status to completed
                    document.processing_status = "completed"
                    document.metadata["processing_completed_at"] = datetime.utcnow().isoformat()
                    document.metadata["chunk_count"] = len(chunks)
                    db.commit()
                    
                except Exception as e:
                    # Update document status to failed
                    document.processing_status = "failed"
                    document.error_message = str(e)
                    document.metadata["processing_error"] = str(e)
                    document.metadata["processing_failed_at"] = datetime.utcnow().isoformat()
                    db.commit()
                    
                    # Log error
                    import logging
                    logging.error(f"Document processing failed for {document_id}: {str(e)}")
        except Exception as e:
            # Log error but don't raise (background task)
            import logging
            logging.error(f"Background processing error for document {document_id}: {str(e)}")
        finally:
            db.close()
    
    def _get_optimal_chunk_size(self, document_size: int) -> int:
        """
        Determine optimal chunk size based on document size.
        
        Args:
            document_size: Size of document in bytes
            
        Returns:
            Optimal chunk size in characters
        """
        # Default chunk size
        default_chunk_size = 1000
        
        # For small documents (< 10KB), use smaller chunks
        if document_size < 10 * 1024:
            return 500
        # For medium documents (10KB - 100KB), use default
        elif document_size < 100 * 1024:
            return default_chunk_size
        # For large documents (100KB - 1MB), use larger chunks
        elif document_size < 1024 * 1024:
            return 1500
        # For very large documents (> 1MB), use even larger chunks
        else:
            return 2000
    
    async def _save_chunks_to_db(
        self,
        db: Session,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> None:
        """
        Save document chunks to database.
        
        Args:
            db: Database session
            document_id: Document ID
            chunks: List of document chunks
        """
        # Delete existing chunks if any
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        
        # Add new chunks
        for i, chunk in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                text=chunk["text"],
                embedding=chunk.get("embedding"),
                metadata=chunk.get("metadata", {})
            )
            db.add(db_chunk)
        
        db.commit()
    
    async def get_document(self, db: Session, document_id: str, user_id: str) -> Optional[Document]:
        """
        Get document by ID.
        
        Args:
            db: Database session
            document_id: Document ID
            user_id: User ID
            
        Returns:
            Document object or None if not found
        """
        return db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
    
    async def list_documents(self, db: Session, user_id: str) -> List[Document]:
        """
        List all documents for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of Document objects
        """
        return db.query(Document).filter(Document.user_id == user_id).all()
    
    async def delete_document(self, db: Session, document_id: str, user_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            db: Database session
            document_id: Document ID
            user_id: User ID
            
        Returns:
            True if deletion was successful
        """
        # Get document
        document = await self.get_document(db, document_id, user_id)
        if not document:
            return False
        
        try:
            # Delete file from storage
            await self.storage_service.delete_file(document.file_path)
            
            # Delete document from database (will cascade to chunks)
            db.delete(document)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            raise e
    
    async def get_document_content(self, db: Session, document_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get document content.
        
        Args:
            db: Database session
            document_id: Document ID
            user_id: User ID
            
        Returns:
            Document content
        """
        # Get document
        document = await self.get_document(db, document_id, user_id)
        if not document:
            return None
        
        # Check if document is processed
        if document.processing_status != "completed":
            return {
                "document_id": document_id,
                "status": document.processing_status,
                "error": document.error_message if document.processing_status == "failed" else None
            }
        
        # Get chunks
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
        
        # Combine chunks into full text
        full_text = "\n\n".join([chunk.text for chunk in chunks])
        
        return {
            "document_id": document_id,
            "content": full_text,
            "chunk_count": len(chunks),
            "status": document.processing_status
        }
