from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import research
from app.schemas.research import (
    AnalyzeTextRequest, AnalyzeTextResponse,
    CitationRequest, CitationResponse,
    VisualizationRequest, VisualizationResponse,
    ReferenceRequest, ReferenceResponse
)

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeTextResponse)
async def analyze_text(
    request: AnalyzeTextRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Analyze text content to extract insights, summaries, or key points
    """
    try:
        analysis = await research.analyze_text(
            text=request.text,
            analysis_type=request.analysis_type
        )
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing text: {str(e)}"
        )


@router.post("/citations", response_model=CitationResponse)
async def generate_citations(
    request: CitationRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate in-line citations and references for a given text
    """
    try:
        result = await research.generate_citations(
            text=request.text,
            style=request.style
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating citations: {str(e)}"
        )


@router.post("/visualize", response_model=VisualizationResponse)
async def generate_visualization(
    request: VisualizationRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate visualizations (charts or tables) from text data
    """
    try:
        result = await research.generate_visualizations(
            text=request.text,
            data_type=request.data_type,
            chart_type=request.chart_type
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating visualization: {str(e)}"
        )


@router.post("/references", response_model=ReferenceResponse)
async def generate_references(
    request: ReferenceRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate references in a specific citation style
    """
    try:
        result = await research.generate_references_only(
            text=request.text,
            style=request.style,
            count=request.count
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating references: {str(e)}"
        )
