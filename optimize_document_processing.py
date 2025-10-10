#!/usr/bin/env python3
"""
Script to optimize document processing in the Doztra backend service.
This script applies optimizations to improve document upload and processing speed.
"""

import os
import sys
import asyncio
from pathlib import Path
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
try:
    from app.services import openai_service
    from app.api.routes import documents
    MODULE_IMPORT_SUCCESS = True
except ImportError:
    logger.warning("Could not import project modules. Running in standalone mode.")
    MODULE_IMPORT_SUCCESS = False

def optimize_document_upload():
    """
    Optimize the document upload functionality.
    """
    logger.info("Optimizing document upload...")
    
    # Create optimized version of the upload function
    optimized_code = """
# Optimized document upload function
@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document for processing.
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(ALLOWED_FILE_TYPES.keys())}"
            )
            
        # Generate document ID
        document_id = f"doc-{uuid4()}"
        
        # Create user directory if it doesn't exist
        user_dir = UPLOAD_DIR / str(current_user.id)
        user_dir.mkdir(exist_ok=True)
        
        # Create document directory
        doc_dir = user_dir / document_id
        doc_dir.mkdir(exist_ok=True)
        
        # Save file with original name
        file_extension = ALLOWED_FILE_TYPES[file.content_type]
        original_filename = file.filename or f"document{file_extension}"
        file_path = doc_dir / original_filename
        
        # Save uploaded file - OPTIMIZED: Use async file operations
        # Read file content into memory first to avoid blocking I/O
        file_content = await file.read()
        
        # Write to disk using a separate thread to avoid blocking
        def write_file():
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
        
        # Run file writing in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, write_file)
            
        # Parse metadata if provided
        meta_dict = {}
        if metadata:
            import json
            try:
                meta_dict = json.loads(metadata)
            except:
                # If JSON parsing fails, use as-is
                meta_dict = {"raw_metadata": metadata}
                
        # Add basic metadata
        meta_dict.update({
            "original_filename": original_filename,
            "content_type": file.content_type,
            "upload_date": datetime.now().isoformat(),
            "user_id": str(current_user.id),
            "conversation_id": conversation_id
        })
        
        # Schedule background processing with priority
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            file.content_type,
            document_id,
            str(current_user.id),
            meta_dict
        )
        
        # Return immediate response
        return {
            "document_id": document_id,
            "file_name": original_filename,
            "file_type": file.content_type,
            "file_size": len(file_content),  # OPTIMIZED: Use in-memory size instead of disk I/O
            "upload_date": meta_dict["upload_date"],
            "status": "uploaded",
            "message": "Document uploaded successfully and queued for processing."
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
"""
    
    # Write optimized code to a file
    with open("app/api/routes/documents_optimized.py", "w") as f:
        f.write(optimized_code)
    
    logger.info("Document upload optimization complete.")

def optimize_document_processing():
    """
    Optimize the document processing functionality.
    """
    logger.info("Optimizing document processing...")
    
    # Create optimized version of the processing function
    optimized_code = """
# Optimized document processing function
async def process_document(file_path: str, file_type: str, document_id: str, user_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process a document: extract text, chunk it, generate embeddings, and store in vector database.
    OPTIMIZED version with improved performance.
    
    Args:
        file_path: Path to the document file
        file_type: MIME type of the file
        document_id: Unique ID for the document
        user_id: ID of the user who uploaded the document
        metadata: Additional metadata about the document
        
    Returns:
        Dict[str, Any]: Processing results including chunk count and status
    """
    try:
        # OPTIMIZATION: Use a semaphore to limit concurrent processing
        # This prevents overloading the system with too many concurrent document processing tasks
        async with PROCESSING_SEMAPHORE:
            # Extract text from document
            text = await extract_text_from_document(file_path, file_type)
            
            # Prepare document metadata
            doc_metadata = {
                "document_id": document_id,
                "user_id": user_id,
                "file_type": file_type,
                "processed_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # OPTIMIZATION: Determine optimal chunk size based on document length
            # Smaller documents can use larger chunks to reduce overhead
            if len(text) < 10000:  # Small document
                chunk_size = MAX_CHUNK_SIZE
                overlap = 100
            elif len(text) < 50000:  # Medium document
                chunk_size = MAX_CHUNK_SIZE
                overlap = 200
            else:  # Large document
                chunk_size = MAX_CHUNK_SIZE // 2
                overlap = 300
            
            # Chunk the document with optimized parameters
            chunks = await chunk_document(text, doc_metadata, chunk_size, overlap)
            
            # Extract just the text for embedding
            chunk_texts = [chunk["text"] for chunk in chunks]
            
            # OPTIMIZATION: Process embeddings in parallel batches
            embeddings = await generate_embeddings_parallel(chunk_texts)
            
            # Add embeddings to chunks
            for i, embedding in enumerate(embeddings):
                chunks[i]["embedding"] = embedding
            
            # Store in vector database
            await store_document_chunks(chunks, document_id, user_id)
            
            # OPTIMIZATION: Update document status immediately
            await update_document_status(document_id, user_id, "ready")
            
            return {
                "document_id": document_id,
                "chunk_count": len(chunks),
                "status": "processed",
                "text_length": len(text),
                "processed_at": doc_metadata["processed_at"]
            }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        # OPTIMIZATION: Update document status to failed
        await update_document_status(document_id, user_id, "failed")
        raise Exception(f"Failed to process document: {str(e)}")

# OPTIMIZATION: Add a semaphore to limit concurrent processing
PROCESSING_SEMAPHORE = asyncio.Semaphore(5)  # Allow up to 5 concurrent document processing tasks

# OPTIMIZATION: Add function to update document status
async def update_document_status(document_id: str, user_id: str, status: str):
    """Update the processing status of a document."""
    # In a real implementation, this would update a database record
    # For now, we'll just create a status file
    status_dir = Path("./document_status")
    status_dir.mkdir(exist_ok=True)
    
    status_file = status_dir / f"{document_id}_status.json"
    with open(status_file, "w") as f:
        import json
        json.dump({
            "document_id": document_id,
            "user_id": user_id,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }, f)

# OPTIMIZATION: Parallel embedding generation
async def generate_embeddings_parallel(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks in parallel batches.
    
    Args:
        texts: List of text chunks to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    try:
        # Process in optimized batches
        embeddings = []
        batch_size = 20  # Adjust based on API limits
        
        # Create tasks for each batch
        tasks = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            tasks.append(generate_batch_embeddings(batch))
        
        # Run all batches concurrently
        batch_results = await asyncio.gather(*tasks)
        
        # Combine results
        for batch_embedding in batch_results:
            embeddings.extend(batch_embedding)
                
        return embeddings
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise Exception(f"Failed to generate embeddings: {str(e)}")

async def generate_batch_embeddings(batch: List[str]) -> List[List[float]]:
    """Generate embeddings for a single batch of texts."""
    # Call OpenAI API to generate embeddings
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=batch
    )
    
    # Extract embedding data
    return [data.embedding for data in response.data]
"""
    
    # Write optimized code to a file
    with open("app/services/openai_service_optimized.py", "w") as f:
        f.write(optimized_code)
    
    logger.info("Document processing optimization complete.")

def apply_optimizations():
    """
    Apply all optimizations to the codebase.
    """
    logger.info("Applying document processing optimizations...")
    
    # Create backup directory
    backup_dir = Path("./backups/document_processing")
    backup_dir.mkdir(exist_ok=True, parents=True)
    
    # Backup original files
    if os.path.exists("app/api/routes/documents.py"):
        shutil.copy("app/api/routes/documents.py", backup_dir / "documents.py.bak")
    
    if os.path.exists("app/services/openai_service.py"):
        shutil.copy("app/services/openai_service.py", backup_dir / "openai_service.py.bak")
    
    # Apply optimizations
    optimize_document_upload()
    optimize_document_processing()
    
    logger.info("All optimizations applied. Backups saved to ./backups/document_processing/")
    logger.info("To use the optimized code, update the imports in main.py to use the optimized versions.")

def main():
    """Main function."""
    logger.info("Document processing optimization script")
    
    # Check if we're running in the correct directory
    if not os.path.exists("app") or not os.path.exists("app/api"):
        logger.error("This script must be run from the project root directory.")
        sys.exit(1)
    
    # Apply optimizations
    apply_optimizations()
    
    # Print recommendations
    print("\n=== OPTIMIZATION RECOMMENDATIONS ===")
    print("1. Use async file operations for document uploads")
    print("2. Limit concurrent document processing with semaphores")
    print("3. Optimize chunk size based on document length")
    print("4. Process embeddings in parallel batches")
    print("5. Update document status immediately after processing")
    print("6. Add proper error handling and status updates")
    print("7. Use in-memory operations instead of disk I/O when possible")
    print("8. Add caching for frequently accessed documents")
    print("9. Implement document processing priority queue")
    print("10. Add progress tracking for large document processing")

if __name__ == "__main__":
    main()
