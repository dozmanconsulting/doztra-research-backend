"""
System Information API Routes
Provides information about available features and dependencies
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from app.services.document_processing import DocumentProcessor
from app.services.vector_search import MilvusVectorService
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/capabilities")
async def get_system_capabilities(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system capabilities and available features"""
    
    # Document processing capabilities
    doc_processor = DocumentProcessor()
    supported_formats = doc_processor.get_supported_formats()
    
    # Vector search capabilities
    vector_service = MilvusVectorService()
    
    # Check API integrations
    import os
    api_keys_available = {
        "assemblyai": bool(os.getenv("ASSEMBLYAI_API_KEY")),
        "firecrawl": bool(os.getenv("FIRECRAWL_API_KEY")),
        "youtube": bool(os.getenv("YOUTUBE_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }
    
    # Database connectivity
    database_available = True  # If we got here, DB is working
    
    # Milvus/Zilliz connectivity
    try:
        milvus_available = await vector_service.connect()
        if milvus_available:
            vector_service.disconnect()
    except Exception as e:
        logger.warning(f"Milvus connection check failed: {e}")
        milvus_available = False
    
    return {
        "success": True,
        "capabilities": {
            "document_processing": {
                "available": True,
                "supported_formats": supported_formats,
                "total_formats": len([k for k, v in supported_formats.items() if v])
            },
            "vector_search": {
                "available": milvus_available,
                "provider": "Zilliz Cloud" if os.getenv("MILVUS_USE_SECURE") == "true" else "Local Milvus"
            },
            "api_integrations": api_keys_available,
            "database": {
                "available": database_available,
                "type": "PostgreSQL"
            }
        },
        "recommendations": _get_recommendations(supported_formats, api_keys_available, milvus_available)
    }

@router.get("/health/detailed")
async def get_detailed_health() -> Dict[str, Any]:
    """Detailed health check with component status"""
    
    health_status = {
        "status": "healthy",
        "components": {},
        "issues": []
    }
    
    # Check document processing
    doc_processor = DocumentProcessor()
    supported_formats = doc_processor.get_supported_formats()
    missing_formats = [k for k, v in supported_formats.items() if not v]
    
    health_status["components"]["document_processing"] = {
        "status": "healthy" if len(missing_formats) < 3 else "degraded",
        "available_formats": len([k for k, v in supported_formats.items() if v]),
        "missing_formats": missing_formats
    }
    
    if missing_formats:
        health_status["issues"].append(f"Missing document processing libraries: {', '.join(missing_formats)}")
    
    # Check API keys
    import os
    api_keys = {
        "assemblyai": os.getenv("ASSEMBLYAI_API_KEY"),
        "firecrawl": os.getenv("FIRECRAWL_API_KEY"), 
        "youtube": os.getenv("YOUTUBE_API_KEY"),
    }
    
    missing_keys = [k for k, v in api_keys.items() if not v]
    health_status["components"]["api_integrations"] = {
        "status": "healthy" if len(missing_keys) == 0 else "degraded",
        "configured_apis": len([k for k, v in api_keys.items() if v]),
        "missing_apis": missing_keys
    }
    
    if missing_keys:
        health_status["issues"].append(f"Missing API keys: {', '.join(missing_keys)}")
    
    # Check vector search
    try:
        vector_service = MilvusVectorService()
        milvus_connected = await vector_service.connect()
        if milvus_connected:
            vector_service.disconnect()
        
        health_status["components"]["vector_search"] = {
            "status": "healthy" if milvus_connected else "unavailable",
            "connected": milvus_connected
        }
        
        if not milvus_connected:
            health_status["issues"].append("Vector search (Milvus/Zilliz) not available")
            
    except Exception as e:
        health_status["components"]["vector_search"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["issues"].append(f"Vector search error: {str(e)}")
    
    # Overall status
    if health_status["issues"]:
        health_status["status"] = "degraded" if len(health_status["issues"]) < 3 else "unhealthy"
    
    return health_status

def _get_recommendations(supported_formats: Dict[str, bool], api_keys: Dict[str, bool], milvus_available: bool) -> list:
    """Generate recommendations based on system capabilities"""
    recommendations = []
    
    missing_formats = [k for k, v in supported_formats.items() if not v]
    if missing_formats:
        recommendations.append({
            "type": "missing_dependencies",
            "message": f"Install missing document processing libraries for: {', '.join(missing_formats)}",
            "action": "pip install " + " ".join([
                "PyPDF2" if "pdf" in missing_formats else "",
                "python-docx" if "docx" in missing_formats else "",
                "openpyxl" if "xlsx" in missing_formats else "",
                "python-pptx" if "pptx" in missing_formats else "",
                "markdown" if "markdown" in missing_formats else "",
                "pyyaml" if "yaml" in missing_formats else "",
            ]).strip()
        })
    
    missing_apis = [k for k, v in api_keys.items() if not v]
    if missing_apis:
        recommendations.append({
            "type": "missing_api_keys",
            "message": f"Configure API keys for enhanced features: {', '.join(missing_apis)}",
            "action": "Set environment variables for the missing API keys"
        })
    
    if not milvus_available:
        recommendations.append({
            "type": "vector_search_unavailable", 
            "message": "Vector search not available - semantic search features disabled",
            "action": "Configure Milvus or Zilliz Cloud connection"
        })
    
    return recommendations
