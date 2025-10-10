from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log the request for debugging
        logger.info(f"Received request: {request.method} {request.url.path}")
        logger.info(f"Request headers: {request.headers}")
        
        # Get the origin from the request headers
        origin = request.headers.get("origin")
        logger.info(f"Origin: {origin}")
        
        # Define allowed origins
        allowed_origins = settings.CORS_ORIGINS + ["https://doztra-ai.netlify.app", "https://doztra.ai"]
        
        # Check if the origin is allowed
        is_allowed_origin = origin in allowed_origins if origin else False
        cors_origin = origin if is_allowed_origin else "*"
        
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            logger.info("Handling OPTIONS preflight request")
            
            # Get the request headers
            request_headers = request.headers.get("access-control-request-headers")
            request_method = request.headers.get("access-control-request-method")
            
            # Create a response with CORS headers
            response = Response(
                content="",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": cors_origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, X-Requested-With, X-Auth-Token, X-CSRF-Token, Cache-Control",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "600",  # 10 minutes
                    "Vary": "Origin",
                },
            )
            return response
        
        # For non-OPTIONS requests, proceed with the request
        response = await call_next(request)
        
        # Add CORS headers to the response
        if origin and is_allowed_origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        
        return response
