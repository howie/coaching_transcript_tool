
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

# Mount static files directly under FastAPI first
api_app.mount(
    "/static",
    StaticFiles(directory=static_dir),
    name="static"
)

# Configure Flask static settings
frontend_app.static_folder = static_dir
frontend_app.static_url_path = '/static'

# Mount Flask app under FastAPI (this should come after static mounting)
api_app.mount("/", WSGIMiddleware(frontend_app))

# Main application
app = api_app

if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://0.0.0.0:5000")
    print(f"Debug: Static files at {static_dir}")
    print("Available JS files:", os.listdir(os.path.join(static_dir, 'js')))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="debug"
    )
