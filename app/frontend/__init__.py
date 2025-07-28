"""
Frontend package for the Coach Assistant application.

This package contains all the frontend routes and related functionality.
"""
from flask import Blueprint

# Create a Blueprint for frontend routes
frontend_bp = Blueprint('frontend', __name__)

# Import routes after blueprint creation to avoid circular imports
from . import routes
