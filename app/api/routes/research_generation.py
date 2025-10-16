"""
API routes for research generation (improve topic, outline, draft generation)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Any, List, Optional
from datetime import datetime
import json

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import research_generation
from app.schemas.research_generation import (
    ImproveTopicRequest, ImproveTopicResponse,
    AlternativeTopicRequest, AlternativeTopicResponse,
    GenerateOutlineRequest, GenerateOutlineResponse,
    GenerateSourcesRequest, GenerateSourcesResponse,
    GenerateDraftRequest, GenerateDraftResponse,
    UploadDocumentsResponse, ProcessedDocument,
    ErrorResponse
)
from app.utils.document_processor import process_uploaded_file

router = APIRouter()


@router.post("/improve-topic", response_model=ImproveTopicResponse)
async def improve_topic(
    request: ImproveTopicRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Improve a research topic based on user input and context
    
    Takes the user's rough topic/guidelines and generates an improved,
    detailed research topic tailored to their discipline and country.
    """
    try:
        result = await research_generation.improve_topic(
            original_input=request.originalInput,
            research_type=request.type,
            discipline=request.discipline,
            faculty=request.faculty,
            country=request.country,
            citation=request.citation,
            length=request.length
        )
        
        return ImproveTopicResponse(
            success=True,
            improvedTopic=result["improvedTopic"],
            suggestions=result["suggestions"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error in improve_topic endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error improving topic: {str(e)}"
        )


@router.post("/alternative-topic", response_model=AlternativeTopicResponse)
async def alternative_topic(
    request: AlternativeTopicRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate an alternative research topic
    
    Creates a different research topic based on the original input,
    offering a fresh perspective or angle.
    """
    try:
        result = await research_generation.generate_alternative_topic(
            original_input=request.originalInput,
            previous_topic=request.previousTopic,
            research_type=request.type,
            discipline=request.discipline,
            faculty=request.faculty,
            country=request.country
        )
        
        return AlternativeTopicResponse(
            success=True,
            alternativeTopic=result["alternativeTopic"],
            rationale=result["rationale"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error in alternative_topic endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating alternative topic: {str(e)}"
        )


@router.post("/generate-outline", response_model=GenerateOutlineResponse)
async def generate_outline(
    request: GenerateOutlineRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate a comprehensive research outline
    
    Creates a detailed, structured outline tailored to:
    - The user's discipline and faculty
    - Country-specific academic standards
    - Research type and citation style
    - Uploaded documents and guidelines
    """
    try:
        # Convert uploaded documents to dict format
        uploaded_docs = [
            {
                "fileName": doc.fileName,
                "fileType": doc.fileType,
                "content": doc.content
            }
            for doc in (request.uploadedDocuments or [])
        ]
        
        result = await research_generation.generate_outline(
            topic=request.topic,
            research_type=request.type,
            discipline=request.discipline,
            faculty=request.faculty,
            country=request.country,
            citation=request.citation,
            length=request.length,
            research_guidelines=request.researchGuidelines,
            uploaded_documents=uploaded_docs
        )
        
        return GenerateOutlineResponse(
            success=True,
            outline=result["outline"],
            countryStandards=result["countryStandards"],
            disciplineGuidelines=result["disciplineGuidelines"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error in generate_outline endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating outline: {str(e)}"
        )


@router.post("/upload-documents", response_model=UploadDocumentsResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Upload and process documents (PDF, Word, TXT)
    
    Extracts text content from uploaded documents and optionally
    identifies key points and citations.
    """
    try:
        processed_documents = []
        
        # Parse metadata if provided
        meta_dict = json.loads(metadata) if metadata else {}
        
        for file in files:
            # Read file content
            content = await file.read()
            
            # Process the file based on type
            result = await process_uploaded_file(
                file_content=content,
                file_name=file.filename,
                file_type=file.content_type
            )
            
            processed_documents.append(ProcessedDocument(
                fileName=file.filename,
                fileType=file.content_type,
                fileSize=len(content),
                extractedContent=result["content"],
                keyPoints=result.get("keyPoints", []),
                citations=result.get("citations", [])
            ))
        
        return UploadDocumentsResponse(
            success=True,
            processedDocuments=processed_documents,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error in upload_documents endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing documents: {str(e)}"
        )


@router.post("/generate-sources", response_model=GenerateSourcesResponse)
async def generate_sources_endpoint(
    request: GenerateSourcesRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate academic sources/references for research
    
    Creates a list of relevant academic sources that can be used
    for citations in the research paper.
    """
    try:
        result = await research_generation.generate_sources(
            topic=request.topic,
            discipline=request.discipline,
            faculty=request.faculty,
            country=request.country,
            research_type=request.type,
            number_of_sources=request.numberOfSources,
            research_guidelines=request.researchGuidelines
        )
        
        return GenerateSourcesResponse(
            success=True,
            sources=result["sources"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error in generate_sources endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sources: {str(e)}"
        )


@router.post("/generate-draft", response_model=GenerateDraftResponse)
async def generate_draft(
    request: GenerateDraftRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate a full research paper draft
    
    Creates a complete research paper based on the outline and all
    collected parameters. This is a long-running operation.
    """
    try:
        # Convert uploaded documents to dict format
        uploaded_docs = [
            {
                "fileName": doc.fileName,
                "fileType": doc.fileType,
                "content": doc.content
            }
            for doc in (request.uploadedDocuments or [])
        ]
        
        # Convert selected sources to dict format
        selected_sources = [
            {
                "id": source.id,
                "authors": source.authors,
                "year": source.year,
                "title": source.title,
                "publication": source.publication,
                "doi": source.doi,
                "url": source.url,
                "citationKey": source.citationKey
            }
            for source in (request.selectedSources or [])
        ]
        
        result = await research_generation.generate_draft(
            topic=request.topic,
            outline=request.outline,
            research_type=request.type,
            discipline=request.discipline,
            faculty=request.faculty,
            country=request.country,
            citation=request.citation,
            length=request.length,
            sources=request.sources,
            selected_sources=selected_sources,
            research_guidelines=request.researchGuidelines,
            uploaded_documents=uploaded_docs
        )
        
        return GenerateDraftResponse(
            success=True,
            draft=result["draft"],
            metadata=result["metadata"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error in generate_draft endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating draft: {str(e)}"
        )
