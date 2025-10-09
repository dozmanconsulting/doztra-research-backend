"""
WSGI entry point for Render.com deployment.
"""
from app.main import app

# This is for WSGI servers like Gunicorn
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
