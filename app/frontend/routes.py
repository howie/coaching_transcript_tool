"""
Frontend routes for the Coach Assistant application.

This module contains all the Flask routes for the frontend interface.
"""
import os
import json
import tempfile
import requests
from flask import render_template, redirect, session, url_for, flash, request, jsonify
import google_auth_oauthlib.flow
from . import frontend_bp as bp

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
        oauth_flow.redirect_uri = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 
                                              'http://localhost:5000/oauth2callback')
except Exception as e:
    print(f"OAuth configuration error: {e}")
    oauth_flow = None

def get_user_info(access_token):
    """Get user information from Google API"""
    try:
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

@bp.route('/')
def home():
    """Landing page"""
    # Bypass login for now
    user_info = {
        'name': 'Demo User',
        'email': 'demo@example.com',
        'picture': 'https://via.placeholder.com/150',
        'given_name': 'Demo'
    }
    return render_template('index.html', user_info=user_info)

@bp.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    # Bypass login for now
    user_info = {
        'name': 'Demo User',
        'email': 'demo@example.com',
        'picture': 'https://via.placeholder.com/150',
        'given_name': 'Demo'
    }
    return render_template('dashboard.html', 
                         user_info=user_info,
                         active_page='dashboard')

@bp.route('/transcript-converter', methods=['GET'])
def transcript_converter():
    """Transcript converter page"""
    # Bypass login for now
    user_info = {
        'name': 'Demo User',
        'email': 'demo@example.com',
        'picture': 'https://via.placeholder.com/150',
        'given_name': 'Demo'
    }
    
    return render_template('transcript_converter.html', 
                         user_info=user_info,
                         active_page='transcript_converter')

@bp.route('/upload', methods=['POST'])
def upload_transcript():
    """Handle transcript file upload"""
    if "access_token" not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file to temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        # TODO: Process the transcript file
        
        return jsonify({
            'success': True,
            'message': f'File "{file.filename}" uploaded successfully',
            'filename': file.filename
        })
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    finally:
        # Clean up
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@bp.route('/signin')
def signin():
    """Initiate Google OAuth flow"""
    if not oauth_flow:
        flash('Google OAuth not configured', 'error')
        return redirect(url_for('frontend.home'))
    
    oauth_flow.redirect_uri = url_for('frontend.oauth2callback', _external=True).replace('http://', 'https://')
    authorization_url, state = oauth_flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@bp.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback"""
    if not oauth_flow:
        return 'OAuth not configured', 400
    
    if not session.get('state') == request.args.get('state'):
        return 'Invalid state parameter', 400
    
    oauth_flow.fetch_token(authorization_response=request.url.replace('http:', 'https:'))
    session['access_token'] = oauth_flow.credentials.token
    return redirect(url_for('frontend.transcript_converter'))

@bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('frontend.home'))

@bp.route('/icf-marker-analysis')
def icf_marker_analysis():
    """ICF Marker Analysis page (coming soon)"""
    user_info = {
        'name': 'Demo User',
        'email': 'demo@example.com',
        'picture': 'https://via.placeholder.com/150',
        'given_name': 'Demo'
    }
    return render_template('coming_soon.html', 
                         user_info=user_info,
                         feature='ICF Marker Analysis',
                         active_page='icf_marker_analysis')

@bp.route('/ai-insights')
def ai_insights():
    """AI Insights page (coming soon)"""
    user_info = {
        'name': 'Demo User',
        'email': 'demo@example.com',
        'picture': 'https://via.placeholder.com/150',
        'given_name': 'Demo'
    }
    return render_template('coming_soon.html', 
                         user_info=user_info,
                         feature='AI Insights',
                         active_page='ai_insights')
