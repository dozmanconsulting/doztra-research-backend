"""
Fix for the OpenAI service to properly handle document queries.
This module contains the fixed query_with_documents function.
"""

from typing import List, Dict, Any
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Import the document validation service
from app.services.document_service_fix import validate_documents

async def query_with_documents_fixed(query: str, user_id: str, document_ids: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Query the LLM with document context, with improved document validation.
    
    Args:
        query: The user's query
        user_id: ID of the user making the query
        document_ids: Optional list of document IDs to use as context
        options: Additional options for the query (model, temperature, etc.)
        
    Returns:
        Dict[str, Any]: LLM response with citations and metadata
    """
    try:
        # Import the original function to reuse most of its logic
        from app.services.openai_service import query_with_documents as original_query_with_documents
        from app.services.openai_service import generate_standard_response
        
        # Default options
        default_options = {
            "model": "gpt-4-turbo",  # Use a default model if settings not available
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_k": 5  # Number of document chunks to retrieve
        }
        
        # Merge with user options
        query_options = {**default_options, **(options or {})}
        
        # If no document IDs provided, fall back to standard response
        if not document_ids:
            return await generate_standard_response(query, query_options)
        
        # Validate documents before proceeding
        validation_result = await validate_documents(document_ids, user_id)
        
        # If any documents are missing, return a clear error
        if validation_result["missing_documents"]:
            missing_docs = validation_result["missing_documents"]
            return {
                "answer": f"One or more documents were not found. The following document IDs do not exist or are not accessible: {', '.join(missing_docs)}",
                "sources": [],
                "query": query,
                "model": query_options["model"],
                "error": "document_not_found",
                "missing_documents": missing_docs
            }
        
        # If any documents are still processing, return a processing status
        if validation_result["processing_documents"]:
            processing_docs = validation_result["processing_documents"]
            return {
                "answer": f"One or more documents are still being processed. Please try again in a few moments. Processing document IDs: {', '.join(processing_docs)}",
                "sources": [],
                "query": query,
                "model": query_options["model"],
                "processing_status": "pending",
                "processing_documents": processing_docs
            }
        
        # If we have valid documents, proceed with the original function
        # but only use the validated document IDs
        if validation_result["valid_documents"]:
            # Call the original function with validated document IDs
            return await original_query_with_documents(
                query=query,
                user_id=user_id,
                document_ids=validation_result["valid_documents"],
                options=options
            )
        else:
            # No valid documents, fall back to standard response
            return await generate_standard_response(query, query_options)
        
    except Exception as e:
        logger.error(f"Error in fixed query_with_documents: {str(e)}")
        # Return a user-friendly error message
        return {
            "answer": f"An error occurred while processing your query: {str(e)}",
            "sources": [],
            "query": query,
            "model": query_options.get("model", "gpt-4-turbo"),
            "error": "processing_error"
        }
