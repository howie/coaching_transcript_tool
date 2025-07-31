"""
Coach Assistant Application Package

This package initializes the Flask and FastAPI applications and their configurations.
"""
import os
from flask import Flask
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    # 获取当前文件所在目录的绝对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__,
              template_folder=os.path.join(base_dir, 'templates'),
              static_folder=os.path.join(base_dir, 'static'))
    
    # 打印调试信息
    print(f"Template directory: {app.template_folder}")
    print(f"Static directory: {app.static_folder}")
    
    # 检查目录是否存在
    if not os.path.exists(app.template_folder):
        print(f"Warning: Template directory does not exist: {app.template_folder}")
    if not os.path.exists(app.static_folder):
        print(f"Warning: Static directory does not exist: {app.static_folder}")
    
    # 加载配置
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    return app

# Create Flask app
frontend_app = create_app()

# Import and register blueprints
from .frontend import frontend_bp
frontend_app.register_blueprint(frontend_bp)

# Import FastAPI app from api_service
from .api.api_service import app as api_app

# The API routes are already imported via api_service
