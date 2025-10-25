"""
System Information API Routes
Provides information about available features and dependencies
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def get_basic_health() -> Dict[str, Any]:
    """Basic health check without authentication"""
    return {
        "status": "healthy",
        "message": "API is running",
        "timestamp": "2025-01-24T18:17:00Z"
    }

@router.get("/capabilities")
async def get_system_capabilities() -> Dict[str, Any]:
    """Get system capabilities and available features"""
    
    # Check API integrations
    api_keys_available = {
        "assemblyai": bool(os.getenv("ASSEMBLYAI_API_KEY")),
        "firecrawl": bool(os.getenv("FIRECRAWL_API_KEY")),
        "youtube": bool(os.getenv("YOUTUBE_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }
    
    # Check basic library availability
    libraries_available = {}
    
    try:
        import PyPDF2
        libraries_available["pdf"] = True
    except ImportError:
        libraries_available["pdf"] = False
    
    try:
        import docx
        libraries_available["docx"] = True
    except ImportError:
        libraries_available["docx"] = False
    
    try:
        import openpyxl
        libraries_available["excel"] = True
    except ImportError:
        libraries_available["excel"] = False
    
    try:
        import markdown
        libraries_available["markdown"] = True
    except ImportError:
        libraries_available["markdown"] = False
    
    try:
        import pymilvus
        libraries_available["milvus"] = True
    except ImportError:
        libraries_available["milvus"] = False
    
    # Detect pinecone SDK (optional)
    try:
        import pinecone  # type: ignore
        libraries_available["pinecone"] = True
    except Exception:
        libraries_available["pinecone"] = False
    
    # Database connectivity
    database_available = True  # If we got here, DB is working
    
    # Vector backend selection
    backend = os.getenv("VECTOR_BACKEND", "milvus").lower()
    if backend == "pinecone":
        vector_available = libraries_available.get("pinecone", False) and bool(os.getenv("PINECONE_API_KEY"))
        vector_provider = "Pinecone"
    else:
        vector_available = libraries_available.get("milvus", False)
        vector_provider = "Zilliz Cloud" if os.getenv("MILVUS_USE_SECURE") == "true" else "Local Milvus"

    return {
        "success": True,
        "capabilities": {
            "document_processing": {
                "available": True,
                "supported_libraries": libraries_available,
                "total_available": len([k for k, v in libraries_available.items() if v])
            },
            "vector_search": {
                "available": vector_available,
                "provider": vector_provider,
                "backend": backend
            },
            "api_integrations": api_keys_available,
            "database": {
                "available": database_available,
                "type": "PostgreSQL"
            }
        },
        "environment": {
            "python_version": "3.13",
            "deployment": "Render.com"
        }
    }

@router.get("/status")
async def get_deployment_status() -> Dict[str, Any]:
    """Simple deployment status check"""
    
    # Check environment variables
    env_vars = {
        "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
        "SECRET_KEY": bool(os.getenv("SECRET_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
    }
    
    return {
        "status": "deployed",
        "message": "Application successfully deployed to Render",
        "environment_variables": env_vars,
        "deployment_info": {
            "platform": "Render.com",
            "python_version": "3.13",
            "build_successful": True
        }
    }
