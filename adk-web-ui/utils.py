import os
import logging
from flask import Flask, request, session, redirect, url_for
from flask_session import Session

logger = logging.getLogger(__name__)

def setup_app_config(app, config_name):
    """Setup application configuration"""
    from config import config
    app.config.from_object(config[config_name])

    # Ensure session directory exists
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

def setup_session(app):
    """Initialize Flask-Session"""
    Session(app)

def setup_middleware(app):
    """Setup request middleware"""
    @app.before_request
    def require_auth():
        """Middleware to check authentication before each request"""
        # Allow access to auth routes and static files without authentication
        public_endpoints = ['login', 'login_post', 'auth_callback', 'auth_store_tokens',
                           'auth_manual_token', 'health', 'static']

        # Skip auth check for static files and public endpoints
        if request.endpoint in public_endpoints or request.endpoint is None:
            return

        # Check if user is authenticated
        if not session.get('authenticated'):
            logger.info(f"[AUTH CHECK] Unauthenticated access attempt to: {request.endpoint}")
            return redirect(url_for('login'))

    @app.before_request
    def log_request_info():
        if app.debug:
            print(f"\n{'='*70}")
            print(f"REQUEST: {request.method} {request.path}")
            print(f"Endpoint: {request.endpoint}")
            print(f"Session authenticated: {session.get('authenticated', False)}")
            print(f"{'='*70}\n")

def setup_error_handlers(app):
    """Setup error handlers"""
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(e):
        print(f"Internal error: {str(e)}")
        return {'error': 'Internal server error'}, 500