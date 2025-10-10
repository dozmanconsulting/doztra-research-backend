from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log the request for debugging
        logger.info(f"Received request: {request.method} {request.url.path}")
        logger.info(f"Request headers: {request.headers}")
        
        # Get the origin from the request headers
        origin = request.headers.get("origin")
        logger.info(f"Origin: {origin}")
        
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            logger.info("Handling OPTIONS preflight request")
            
            # Create a response with CORS headers
            response = Response(
                content="",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin or "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "600",  # 10 minutes
                },
            )
            return response
        
        # For non-OPTIONS requests, proceed with the request
        response = await call_next(request)
        
        # Add CORS headers to the response
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
