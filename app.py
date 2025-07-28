
from flask import Flask, render_template, redirect, session, url_for, request, flash, jsonify
import google_auth_oauthlib.flow
import json
import os
import requests
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

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

def require_auth():
    """Check if user is authenticated"""
    return "access_token" in session and get_user_info(session["access_token"]) is not None

@app.route('/')
def home():
    """Dashboard home - requires authentication"""
    if not require_auth():
        return render_template('login.html')
    
    user_info = get_user_info(session["access_token"])
    return render_template('dashboard.html', user_info=user_info, current_page='dashboard')

@app.route('/signin')
def signin():
    """Initiate Google OAuth flow"""
    if not oauth_flow:
        flash('Google OAuth not configured', 'error')
        return redirect('/')
    
    oauth_flow.redirect_uri = url_for('oauth2callback', _external=True).replace('http://', 'https://')
    authorization_url, state = oauth_flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback"""
    if not oauth_flow:
        return 'OAuth not configured', 400
    
    if not session.get('state') == request.args.get('state'):
        return 'Invalid state parameter', 400
    
    oauth_flow.fetch_token(authorization_response=request.url.replace('http:', 'https:'))
    session['access_token'] = oauth_flow.credentials.token
    return redirect('/')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect('/')

@app.route('/transcript-converter')
def transcript_converter():
    """Transcript converter page - requires authentication"""
    if not require_auth():
        return redirect('/')
    
    user_info = get_user_info(session["access_token"])
    return render_template('transcript_converter.html', user_info=user_info, current_page='transcript-converter')

@app.route('/marker-analysis')
def marker_analysis():
    """ICF Marker Analysis page - coming soon"""
    if not require_auth():
        return redirect('/')
    
    user_info = get_user_info(session["access_token"])
    return render_template('coming_soon.html', 
                         user_info=user_info, 
                         current_page='marker-analysis',
                         feature_name='ICF Marker Analysis')

@app.route('/insights')
def insights():
    """Insights page - coming soon"""
    if not require_auth():
        return redirect('/')
    
    user_info = get_user_info(session["access_token"])
    return render_template('coming_soon.html', 
                         user_info=user_info, 
                         current_page='insights',
                         feature_name='Coaching Session Insights')

@app.route('/upload', methods=['POST'])
def upload_transcript():
    """Handle transcript file upload"""
    if not require_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    allowed_extensions = {'.vtt', '.srt'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Please upload .vtt or .srt files only.'}), 400
    
    # Process the file (integrate with your existing processor)
    try:
        # For now, return success message - integrate with your existing processor
        return jsonify({
            'success': True,
            'message': f'File "{file.filename}" uploaded successfully. Processing...',
            'filename': file.filename,
            'status': 'processing'
        })
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
