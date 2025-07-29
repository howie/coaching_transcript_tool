"""
Frontend routes for the Coach Assistant application.

This module contains all the Flask routes for the frontend interface.
"""
import os
import json
import tempfile
import requests
import io
from flask import (render_template, redirect, session, url_for, flash, 
                   request, jsonify, send_file)
from . import frontend_bp as bp
from src.coaching_assistant.core.processor import format_transcript, UnrecognizedFormatError

# Google OAuth configuration - disabled for now (using mock login)
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
    # Check if user is logged in (mock)
    user_info = session.get('user_info')
    return render_template('index.html', user_info=user_info)

@bp.route('/login')
def login():
    """Mock login - set session and redirect to dashboard"""
    # Mock user info
    session['user_info'] = {
        'name': 'Demo User',
        'email': 'demo@coachassistant.com',
        'picture': 'https://via.placeholder.com/150',
        'given_name': 'Demo'
    }
    flash('Login successful!', 'success')
    return redirect(url_for('frontend.dashboard'))

@bp.route('/dashboard')
def dashboard():
    """Main dashboard page with feature overview"""
    user_info = session.get('user_info')
    if not user_info:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('frontend.home'))
    
    return render_template('dashboard.html', 
                         user_info=user_info,
                         active_page='dashboard')

@bp.route('/transcript-converter', methods=['GET'])
def transcript_converter():
    """Transcript converter page"""
    user_info = session.get('user_info')
    if not user_info:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('frontend.home'))
    
    return render_template('transcript_converter.html', 
                         user_info=user_info,
                         active_page='transcript_converter')

@bp.route('/upload', methods=['POST'])
def upload_transcript():
    """Handle transcript file upload and conversion."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    coach_name = request.form.get('coach_name')
    client_name = request.form.get('client_name')
    # When manually adding checkbox value, checked checkbox sends 'on'
    convert_chinese = request.form.get('convert_to_traditional_chinese') == 'on'

    try:
        file_content = file.read()
        original_filename = file.filename
        
        excel_bytes = format_transcript(
            file_content=file_content,
            original_filename=original_filename,
            output_format='excel',
            coach_name=coach_name,
            client_name=client_name,
            convert_to_traditional_chinese=convert_chinese
        )
        
        output_filename = f"processed_{os.path.splitext(original_filename)[0]}.xlsx"
        
        return send_file(
            io.BytesIO(excel_bytes),
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except UnrecognizedFormatError as e:
        return jsonify({'error': f'File format not recognized: {e}'}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@bp.route('/signin')
def signin():
    """Initiate Google OAuth flow"""
    try:
        if not oauth_flow:
            flash('Google OAuth not configured', 'error')
            return redirect(url_for('frontend.home'))
        
        oauth_flow.redirect_uri = url_for('frontend.oauth2callback', _external=True).replace('http://', 'https://')
        authorization_url, state = oauth_flow.authorization_url()
        session['state'] = state
        return redirect(authorization_url)
    except NameError:
        flash('OAuth not available', 'error')
        return redirect(url_for('frontend.home'))

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

@bp.route('/marker-analysis')
def marker_analysis():
    """Marker Analysis page (coming soon)"""
    user_info = session.get('user_info')
    if not user_info:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('frontend.home'))
    
    return render_template('coming_soon.html', 
                         user_info=user_info,
                         feature_name='Marker Analysis',
                         active_page='marker_analysis')

@bp.route('/insights')
def insights():
    """Insights page (coming soon)"""
    user_info = session.get('user_info')
    if not user_info:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('frontend.home'))
    
    return render_template('coming_soon.html', 
                         user_info=user_info,
                         feature_name='Insights',
                         active_page='insights')

@bp.route('/profile')
def profile():
    """Profile page (coming soon)"""
    user_info = session.get('user_info')
    if not user_info:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('frontend.home'))
    
    return render_template('coming_soon.html', 
                         user_info=user_info,
                         feature_name='Profile',
                         active_page='profile')

@bp.route('/feedback')
def feedback():
    """Feedback page (coming soon)"""
    user_info = session.get('user_info')
    if not user_info:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('frontend.home'))
    
    return render_template('coming_soon.html', 
                         user_info=user_info,
                         feature_name='Feedback',
                         active_page='feedback')
