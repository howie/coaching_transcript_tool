
"""
Main entry point for the Coach Assistant application.

This module initializes and runs the FastAPI and Flask applications.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Flask frontend and FastAPI app
from app import frontend_app
from app.api.api_service import app as api_service

# Create main FastAPI application
main_app = FastAPI(title="Coach Assistant", version="1.0.0")

# Configure static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app/static")

# Mount static files
main_app.mount(
    "/static",
    StaticFiles(directory=static_dir),
    name="static"
)

# Configure Flask static settings
frontend_app.static_folder = static_dir
frontend_app.static_url_path = '/static'

# Mount API under /api prefix
main_app.mount("/api", api_service)

# Mount Flask app for all other routes (this should be last)
main_app.mount("/", WSGIMiddleware(frontend_app))

# Main application
app = main_app

if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://0.0.0.0:5000")
    print(f"Debug: Static files at {static_dir}")
    if os.path.exists(os.path.join(static_dir, 'js')):
        print("Available JS files:", os.listdir(os.path.join(static_dir, 'js')))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="debug"
    )
