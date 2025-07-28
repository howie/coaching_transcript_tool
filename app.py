
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

@app.route('/')
def home():
    """Landing page"""
    user_info = None
    if "access_token" in session:
        user_info = get_user_info(session["access_token"])
    return render_template('index.html', user_info=user_info)

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
    return redirect('/transcript-converter')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')

@app.route('/transcript-converter')
def transcript_converter():
    """Transcript converter page - requires authentication"""
    if "access_token" not in session:
        flash('Please sign in to access the transcript converter', 'info')
        return redirect('/')
    
    user_info = get_user_info(session["access_token"])
    if not user_info:
        session.clear()
        flash('Session expired. Please sign in again.', 'error')
        return redirect('/')
    
    return render_template('transcript_converter.html', user_info=user_info)

@app.route('/upload', methods=['POST'])
def upload_transcript():
    """Handle transcript file upload"""
    if "access_token" not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # For now, return success message - integrate with your existing processor later
    return jsonify({
        'success': True,
        'message': f'File "{file.filename}" uploaded successfully. Processing will be implemented soon.',
        'filename': file.filename
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
