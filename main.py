
import os
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask, render_template, redirect, session, url_for, request, flash, jsonify
import google_auth_oauthlib.flow
import json
import requests

# Create FastAPI app
api_app = FastAPI(
    title="CoachAssistant API",
    description="AI-powered coaching tools API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Create Flask app for frontend
frontend_app = Flask(__name__)
frontend_app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Google OAuth configuration
try:
    oauth_config = json.loads(os.environ.get('GOOGLE_OAUTH_SECRETS', '{}'))
    if oauth_config:
        oauth_flow = google_auth_oauthlib.flow.Flow.from_client_config(
            oauth_config,
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "openid", 
                "https://www.googleapis.com/auth/userinfo.profile",
            ]
        )
except:
    oauth_flow = None

def get_user_info(access_token):
    """Get user information from Google API"""
    try:
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
        )
        return response.json() if response.status_code == 200 else None
    except:
        return None

# Flask routes
@frontend_app.route('/')
def dashboard():
    """Main dashboard page"""
    # Remove authentication requirement - go directly to dashboard
    mock_user_info = {
        'given_name': 'User',
        'name': 'Anonymous User',
        'email': 'user@example.com'
    }
    return render_template('dashboard.html', user_info=mock_user_info)

@frontend_app.route('/transcript-converter')
def transcript_converter():
    """Transcript converter page - no authentication required"""
    mock_user_info = {
        'given_name': 'User',
        'name': 'Anonymous User',
        'email': 'user@example.com'
    }
    return render_template('transcript_converter.html', user_info=mock_user_info)

@frontend_app.route('/marker-analysis')
def marker_analysis():
    """ICF Marker Analysis page - coming soon"""
    mock_user_info = {
        'given_name': 'User',
        'name': 'Anonymous User',
        'email': 'user@example.com'
    }
    return render_template('coming_soon.html', user_info=mock_user_info, feature="ICF Marker Analysis")

@frontend_app.route('/insights')
def insights():
    """Insights page - coming soon"""
    mock_user_info = {
        'given_name': 'User',
        'name': 'Anonymous User',
        'email': 'user@example.com'
    }
    return render_template('coming_soon.html', user_info=mock_user_info, feature="Insights")

@frontend_app.route('/signin')
def signin():
    """Initiate Google OAuth flow"""
    if not oauth_flow:
        flash('OAuth not configured', 'error')
        return redirect('/')
    
    oauth_flow.redirect_uri = url_for('oauth_callback', _external=True)
    authorization_url, state = oauth_flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@frontend_app.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback"""
    if not oauth_flow:
        flash('OAuth not configured', 'error')
        return redirect('/')
    
    oauth_flow.redirect_uri = url_for('oauth_callback', _external=True)
    authorization_response = request.url
    oauth_flow.fetch_token(authorization_response=authorization_response)
    
    credentials = oauth_flow.credentials
    session['access_token'] = credentials.token
    
    flash('Successfully signed in!', 'success')
    return redirect('/')

@frontend_app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')

# FastAPI routes
from fastapi import File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from coaching_assistant.core.processor import format_transcript
from coaching_assistant.parser import UnrecognizedFormatError

logger = logging.getLogger(__name__)

@api_app.post("/api/convert-transcript")
async def convert_transcript(
    file: UploadFile = File(..., description="The VTT or SRT transcript file to process."),
    coach_name: Optional[str] = Form(None, description="Name of the coach to be replaced with 'Coach'."),
    client_name: Optional[str] = Form(None, description="Name of the client to be replaced with 'Client'."),
    convert_to_traditional_chinese: bool = Form(False, description="Convert Simplified Chinese to Traditional Chinese."),
):
    """Convert transcript file to Excel format"""
    logger.info(f"Received request to convert '{file.filename}' to Excel")
    
    try:
        file_content = await file.read()
        
        result = format_transcript(
            file_content=file_content,
            original_filename=file.filename,
            output_format="excel",
            coach_name=coach_name,
            client_name=client_name,
            convert_to_traditional_chinese=convert_to_traditional_chinese,
        )
        
        filename = file.filename or "transcript"
        output_filename = f"{filename.rsplit('.', 1)[0]}.xlsx"
        
        logger.info(f"Successfully converted file. Preparing response as {output_filename}")
        
        # Create BytesIO object from the result bytes
        excel_stream = io.BytesIO(result)
        excel_stream.seek(0)
        
        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except UnrecognizedFormatError as e:
        logger.warning(f"Returning 400 due to unrecognized format: {e}")
        raise HTTPException(status_code=400, detail=f"Unrecognized file format: {e}")
    except Exception as e:
        logger.exception(f"Error processing file {file.filename}:")
        raise HTTPException(status_code=500, detail=str(e))

@api_app.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get status of async job (placeholder for future implementation)"""
    return {"job_id": job_id, "status": "completed", "message": "Job status endpoint - coming soon"}

# Mount Flask app under FastAPI
api_app.mount("/", WSGIMiddleware(frontend_app))

# ASGI application
app = api_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
