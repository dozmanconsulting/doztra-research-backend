
@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a document.
    
    This endpoint deletes a document and all associated files.
    """
    try:
        # Check if document exists
        user_dir = UPLOAD_DIR / str(current_user.id)
        doc_dir = user_dir / document_id
        
        if not doc_dir.exists():
            # Check if document ID format is valid
            if not document_id.startswith("doc-"):
                raise HTTPException(status_code=400, detail="Invalid document ID format")
            
            # Document directory doesn't exist, but let's check if there are any chunks
            chunks_dir = Path("./document_chunks")
            chunks_file = chunks_dir / f"{document_id}_chunks.json"
            
            if chunks_file.exists():
                # Delete chunks file
                chunks_file.unlink()
                logger.info(f"Deleted chunks file for document {document_id}")
                return {"message": "Document chunks deleted successfully"}
            else:
                # Document truly doesn't exist
                raise HTTPException(status_code=404, detail="Document not found")
        
        # Document exists, proceed with deletion
        
        # Get list of files before deletion for logging
        files = list(doc_dir.glob("*"))
        file_names = [f.name for f in files]
        logger.info(f"Deleting document {document_id} with files: {file_names}")
        
        # Delete document directory
        try:
            shutil.rmtree(doc_dir)
            logger.info(f"Deleted document directory for {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document directory: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete document directory: {str(e)}")
        
        # Delete chunks file if it exists
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        if chunks_file.exists():
            try:
                chunks_file.unlink()
                logger.info(f"Deleted chunks file for document {document_id}")
            except Exception as e:
                logger.error(f"Error deleting chunks file: {str(e)}")
                # Don't fail the request if only the chunks deletion fails
        
        # Delete any other associated files
        # For example, status files
        status_dir = Path("./document_status")
        if status_dir.exists():
            status_file = status_dir / f"{document_id}_status.json"
            if status_file.exists():
                try:
                    status_file.unlink()
                    logger.info(f"Deleted status file for document {document_id}")
                except Exception as e:
                    logger.error(f"Error deleting status file: {str(e)}")
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in delete_document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
