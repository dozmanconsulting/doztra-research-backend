from fastapi import FastAPI, Request, status, Depends, Header, Cookie, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from app.models.user import UserRole
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import json
import logging
from typing import Optional

from app.api.routes import auth, users, token_usage, user_preferences, usage_statistics, admin, subscription_plans, chat, research_projects, research_content, documents, document_queries, research, research_options, content_feedback
from app.core.config import settings
from app.services.auth import get_current_user, verify_token
from app.services.admin import verify_admin_token, security
from app.db.session import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security scheme is imported from admin service

# Create FastAPI app with enhanced metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Authentication service for Doztra AI Platform",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url=None,  # Disable default OpenAPI endpoint
    contact={
        "name": "Doztra AI Support",
        "url": "https://doztra.ai/support",
        "email": "support@doztra.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://doztra.ai/terms",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["User Management"])
app.include_router(token_usage.router, prefix="/api/tokens", tags=["Token Usage"])
app.include_router(user_preferences.router, prefix="/api/preferences", tags=["User Preferences"])
app.include_router(usage_statistics.router, prefix="/api/usage", tags=["Usage Statistics"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])
app.include_router(subscription_plans.router, prefix="/api/subscription", tags=["Subscription Plans"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(research_projects.router, prefix="/api/research/projects", tags=["Research Projects"])
app.include_router(research_content.router, prefix="/api/research/content", tags=["Research Content"])
app.include_router(research_options.router, prefix="/api/research/options", tags=["Research Options"])
app.include_router(research.router, prefix="/api/research", tags=["Research Tools"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(document_queries.router, prefix="/api/documents", tags=["Document Queries"])
app.include_router(content_feedback.router, prefix="/api", tags=["Content Feedback"])

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        errors.append(error_detail)
    
    logger.error(f"Validation error: {json.dumps(errors)}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": errors,
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
        terms_of_service=app.terms_of_service,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Optional security for routes that should redirect instead of returning 401/403
class OptionalHTTPBearer(HTTPBearer):
    def __init__(self, auto_error: bool = False):
        super().__init__(auto_error=auto_error)

optional_security = OptionalHTTPBearer(auto_error=False)

# Helper function to check admin authorization is imported from admin service

# OpenAPI schema endpoint - public for Swagger UI to work
@app.get("/api/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    try:
        schema = app.openapi()
        return JSONResponse(content=schema)
    except Exception as e:
        logger.error(f"Error generating OpenAPI schema: {e}")
        return JSONResponse(
            content={"detail": "Error generating API schema"},
            status_code=500
        )

# Custom Swagger UI route - GET method (public access)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html_get(request: Request):
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico"
    )

# Helper function to handle docs requests
async def handle_docs_request(request: Request, credentials: Optional[HTTPAuthorizationCredentials], doc_type: str):
    token = None
    
    # Check if this is a POST request with token
    if request.method == "POST":
        form_data = await request.form()
        token = form_data.get("token")
        if token:
            # Get database session
            db = next(get_db())
            try:
                # Get the user from the token
                user = await verify_token(token=token, db=db)
                # Check if user has admin role
                if user.role == UserRole.ADMIN:
                    # Valid admin token, proceed
                    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                else:
                    return RedirectResponse(
                        url=f"/admin-login?redirect=/{doc_type}&error=not_admin",
                        status_code=status.HTTP_303_SEE_OTHER
                    )
            except HTTPException:
                return RedirectResponse(
                    url=f"/admin-login?redirect=/{doc_type}&error=invalid_token",
                    status_code=status.HTTP_303_SEE_OTHER
                )
    
    # For GET requests or if no valid token in POST
    if not credentials:
        return RedirectResponse(
            url=f"/admin-login?redirect=/{doc_type}",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    try:
        # Get database session
        db = next(get_db())
        # Get the user from the token
        user = await verify_token(token=credentials.credentials, db=db)
        # Check if user has admin role
        if user.role != UserRole.ADMIN:
            return RedirectResponse(
                url=f"/admin-login?redirect=/{doc_type}",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Generate the appropriate HTML based on doc_type
        if doc_type == "docs":
            return generate_swagger_ui_html(token=credentials.credentials)
        elif doc_type == "redoc":
            return generate_redoc_html(token=credentials.credentials)
        else:
            # Default to Swagger UI
            return generate_swagger_ui_html(token=credentials.credentials)
            
    except HTTPException:
        return RedirectResponse(
            url=f"/admin-login?redirect=/{doc_type}",
            status_code=status.HTTP_303_SEE_OTHER
        )

# Custom ReDoc route (admin only) - GET method
@app.get("/redoc", include_in_schema=False)
async def redoc_html_get(request: Request):
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico",
    )

# Function to generate ReDoc HTML with embedded token
def generate_redoc_html(token=None):
    redoc = get_redoc_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico",
    )
    
    # Add script to automatically use token from sessionStorage for API calls
    redoc_content = redoc.body.decode()
    token_script = f"""
    <script>
        // Add token from sessionStorage to API requests
        window.addEventListener('DOMContentLoaded', function() {{
            const token = sessionStorage.getItem('admin_token') || '{token or ""}';
            if (token) {{
                // Override fetch to add authorization header
                const originalFetch = window.fetch;
                window.fetch = function(url, options) {{
                    options = options || {{}};
                    options.headers = options.headers || {{}};
                    
                    // Add authorization header for API calls
                    if (url.includes('/api/')) {{
                        options.headers['Authorization'] = `Bearer ${token}`;
                    }}
                    
                    return originalFetch(url, options);
                }};
            }}
        }});
    </script>
    """
    modified_content = redoc_content.replace("</body>", f"{token_script}</body>")
    return HTMLResponse(content=modified_content)

# Function to generate Swagger UI HTML with embedded token
def generate_swagger_ui_html(token=None):
    swagger_ui = get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico"
    )
    
    # Add script to automatically use token from sessionStorage
    swagger_ui_content = swagger_ui.body.decode()
    token_script = f"""
    <script>
        // Add token from sessionStorage to Swagger UI auth
        window.addEventListener('DOMContentLoaded', function() {{  
            setTimeout(function() {{
                const token = sessionStorage.getItem('admin_token') || '{token or ""}';
                if (token) {{
                    const authBtn = document.querySelector('.swagger-ui .auth-wrapper .authorize');
                    if (authBtn) {{
                        authBtn.click();
                        setTimeout(function() {{
                            const tokenInput = document.querySelector('.swagger-ui .auth-container input');
                            const authorizeBtn = document.querySelector('.swagger-ui .auth-btn-wrapper .authorize');
                            if (tokenInput && authorizeBtn) {{
                                tokenInput.value = token;
                                authorizeBtn.click();
                                document.querySelector('.swagger-ui .dialog-ux .modal-ux-header .close-modal').click();
                            }}
                        }}, 300);
                    }}
                }}
            }}, 1000);
        }});
    </script>
    """
    modified_content = swagger_ui_content.replace("</body>", f"{token_script}</body>")
    return HTMLResponse(content=modified_content)

# API landing page (public)
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to Doztra Auth Service API"}

@app.get("/editor", response_class=HTMLResponse, include_in_schema=False)
async def content_editor(request: Request):
    """
    Serve the content editor HTML page.
    """
    return templates.TemplateResponse("content-editor.html", {"request": request})

# Admin login page (public)
@app.get("/admin-login", include_in_schema=False)
async def admin_login_page(request: Request):
    """
    Serve the admin login page.
    """ 
    with open("app/static/admin-login.html", "r") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)

# Admin dashboard page
@app.get("/admin/dashboard", include_in_schema=False)
async def admin_dashboard_page(request: Request):
    """
    Serve the admin dashboard page.
    """
    return templates.TemplateResponse("admin-dashboard.html", {"request": request})

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(request: Request):
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        dict: Status information including service name and current status
    """
    return {
        "status": "healthy",
        "service": "doztra-auth-service",
        "version": app.version,
        "timestamp": datetime.utcnow().isoformat(),
        "host": request.headers.get("host", "unknown")
    }

# Redirect from port 8000 to 8001 for docs
@app.get("/redirect-docs", include_in_schema=False)
async def redirect_docs(request: Request):
    """
    Redirect from port 8000 to 8001 for documentation.
    """
    host = request.headers.get("host", "")
    if host.endswith(":8000"):
        new_host = host.replace(":8000", ":8001")
        return RedirectResponse(url=f"http://{new_host}/docs")
    return RedirectResponse(url="/docs")
