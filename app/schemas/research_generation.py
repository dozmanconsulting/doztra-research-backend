"""
Schemas for research generation endpoints (improve topic, outline generation, etc.)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Improve Topic Schemas
# ============================================================================

class UploadedDocumentInfo(BaseModel):
    """Information about an uploaded document"""
    fileName: str
    fileType: str


class ImproveTopicRequest(BaseModel):
    """Request schema for improving a research topic"""
    originalInput: str = Field(..., description="User's original topic/guidelines")
    type: str = Field(..., description="Research type (Essay, Dissertation, etc.)")
    citation: str = Field(..., description="Citation style (APA 7, MLA 9, etc.)")
    length: str = Field(..., description="Expected length (1-2 pages, 10-20 pages, etc.)")
    discipline: str = Field(..., description="Academic discipline")
    faculty: Optional[str] = Field(None, description="Faculty/specialization")
    country: str = Field(..., description="Country for academic standards")
    uploadedDocuments: Optional[List[UploadedDocumentInfo]] = Field(default=[], description="List of uploaded documents")
    timestamp: str = Field(..., description="Request timestamp")


class ImproveTopicResponse(BaseModel):
    """Response schema for improved topic"""
    success: bool = True
    improvedTopic: str = Field(..., description="Improved research topic")
    suggestions: List[str] = Field(default=[], description="Additional suggestions")
    timestamp: str = Field(..., description="Response timestamp")


# ============================================================================
# Alternative Topic Schemas
# ============================================================================

class AlternativeTopicRequest(BaseModel):
    """Request schema for generating alternative topic"""
    originalInput: str = Field(..., description="User's original input")
    previousTopic: Optional[str] = Field(None, description="Previously generated topic")
    type: str = Field(..., description="Research type")
    discipline: str = Field(..., description="Academic discipline")
    faculty: Optional[str] = Field(None, description="Faculty/specialization")
    country: str = Field(..., description="Country for academic standards")
    timestamp: str = Field(..., description="Request timestamp")


class AlternativeTopicResponse(BaseModel):
    """Response schema for alternative topic"""
    success: bool = True
    alternativeTopic: str = Field(..., description="Alternative research topic")
    rationale: str = Field(..., description="Explanation for the alternative")
    timestamp: str = Field(..., description="Response timestamp")


# ============================================================================
# Generate Outline Schemas
# ============================================================================

class UploadedDocumentContent(BaseModel):
    """Full document information including content"""
    fileName: str
    fileType: str
    content: str


class GenerateOutlineRequest(BaseModel):
    """Request schema for generating research outline"""
    topic: str = Field(..., description="Research topic")
    type: str = Field(..., description="Research type")
    citation: str = Field(..., description="Citation style")
    length: str = Field(..., description="Expected length")
    discipline: str = Field(..., description="Academic discipline")
    faculty: Optional[str] = Field(None, description="Faculty/specialization")
    country: str = Field(..., description="Country for academic standards")
    researchGuidelines: Optional[str] = Field(None, description="Additional research guidelines")
    uploadedDocuments: Optional[List[UploadedDocumentContent]] = Field(default=[], description="Uploaded documents with content")
    timestamp: str = Field(..., description="Request timestamp")


class CountryStandards(BaseModel):
    """Country-specific academic standards"""
    country: str
    specificRequirements: List[str]


class DisciplineGuidelines(BaseModel):
    """Discipline-specific guidelines"""
    discipline: str
    faculty: Optional[str]
    keyFocus: List[str]


class GenerateOutlineResponse(BaseModel):
    """Response schema for generated outline"""
    success: bool = True
    outline: List[str] = Field(..., description="Research paper outline as array of strings")
    countryStandards: CountryStandards = Field(..., description="Country-specific standards applied")
    disciplineGuidelines: DisciplineGuidelines = Field(..., description="Discipline-specific guidelines applied")
    timestamp: str = Field(..., description="Response timestamp")


# ============================================================================
# Upload Documents Schemas
# ============================================================================

class DocumentMetadata(BaseModel):
    """Metadata for document upload"""
    discipline: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None


class ProcessedDocument(BaseModel):
    """Information about a processed document"""
    fileName: str
    fileType: str
    fileSize: int
    extractedContent: str
    keyPoints: List[str] = Field(default=[], description="Key points extracted from document")
    citations: List[str] = Field(default=[], description="Citations found in document")


class UploadDocumentsResponse(BaseModel):
    """Response schema for document upload"""
    success: bool = True
    processedDocuments: List[ProcessedDocument]
    timestamp: str = Field(..., description="Response timestamp")


# ============================================================================
# Generate Draft Schemas
# ============================================================================

class DraftSection(BaseModel):
    """A section of the generated draft"""
    heading: str
    content: str
    wordCount: int


class DraftMetadata(BaseModel):
    """Metadata about the generated draft"""
    generatedAt: str
    processingTime: str
    aiModel: str
    wordCount: int
    pageCount: int
    citationStyle: str
    discipline: str
    country: str


class GenerateDraftRequest(BaseModel):
    """Request schema for generating full draft"""
    topic: str
    outline: List[str]
    type: str
    citation: str
    length: str
    discipline: str
    faculty: Optional[str] = None
    country: str
    sources: str = Field(..., description="Number of sources (3-4, 8-12, etc.)")
    selectedSources: Optional[List[AcademicSource]] = Field(default=[], description="Selected academic sources for citations")
    researchGuidelines: Optional[str] = None
    uploadedDocuments: Optional[List[UploadedDocumentContent]] = Field(default=[])
    timestamp: str


class GenerateDraftResponse(BaseModel):
    """Response schema for generated draft"""
    success: bool = True
    draft: str = Field(..., description="Complete draft in markdown format")
    metadata: DraftMetadata
    timestamp: str


# ============================================================================
# Generate Sources Schemas
# ============================================================================

class AcademicSource(BaseModel):
    """Single academic source/reference"""
    id: str = Field(..., description="Unique identifier for the source")
    authors: List[str] = Field(..., description="List of author names")
    year: int = Field(..., description="Publication year")
    title: str = Field(..., description="Article/book title")
    publication: str = Field(..., description="Journal/publisher name")
    doi: Optional[str] = Field(None, description="DOI if available")
    url: Optional[str] = Field(None, description="URL if available")
    abstract: str = Field(..., description="Brief abstract or summary")
    relevance: str = Field(..., description="Why this source is relevant")
    citationKey: str = Field(..., description="Short citation key (e.g., 'Smith2020')")


class GenerateSourcesRequest(BaseModel):
    """Request schema for generating academic sources"""
    topic: str
    discipline: str
    faculty: Optional[str] = None
    country: str
    type: str
    numberOfSources: str = Field(..., description="Number of sources (3-4, 4-7, 8-12, 12+)")
    researchGuidelines: Optional[str] = None
    timestamp: str


class GenerateSourcesResponse(BaseModel):
    """Response schema for generated sources"""
    success: bool = True
    sources: List[AcademicSource]
    timestamp: str


# ============================================================================
# Error Response Schema
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    code: Optional[str] = None
    timestamp: str
