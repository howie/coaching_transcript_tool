"""
API package for the Coach Assistant application.

This package contains all the API routes and related functionality.
"""
# Import the API service
from .api_service import app as api_app

# For backward compatibility
api_router = api_app.router
