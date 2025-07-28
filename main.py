
"""
Main entry point for the Coach Assistant application.

This module initializes and runs the FastAPI and Flask applications.
"""
import os
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Flask frontend and FastAPI app
from app import frontend_app, api_app

# Configure static files for Flask
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app/static")
frontend_app.static_folder = static_dir
frontend_app.static_url_path = '/static'

# Mount Flask app under FastAPI
api_app.mount("/", WSGIMiddleware(frontend_app))

# Also mount static files directly under FastAPI for better compatibility
api_app.mount(
    "/static",
    StaticFiles(directory=static_dir),
    name="static"
)

# Main application
app = api_app

if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://localhost:8000")
    print(f"Debug: Static files at {static_dir}")
    print("Available JS files:", os.listdir(os.path.join(static_dir, 'js')))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
