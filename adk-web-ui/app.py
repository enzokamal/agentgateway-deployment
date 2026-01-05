from flask import Flask
from flask_session import Session
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --------------------------
# Helper Functions
# --------------------------
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
    from flask import session, request, redirect, url_for

    @app.before_request
    def require_auth():
        """Middleware to check authentication before each request"""
        # Allow access to auth routes and static files without authentication
        public_endpoints = ['auth.login', 'auth.login_post', 'auth.auth_callback', 'auth.auth_store_tokens',
                           'auth.auth_manual_token', 'health.health', 'static']

        # Skip auth check for static files and public endpoints
        if request.endpoint in public_endpoints or request.endpoint is None:
            return

        # Check if user is authenticated
        if not session.get('authenticated'):
            logger.info(f"[AUTH CHECK] Unauthenticated access attempt to: {request.endpoint}")
            return redirect(url_for('auth.login'))

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

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)

    # Setup configuration and components
    setup_app_config(app, config_name)
    setup_session(app)
    setup_middleware(app)
    setup_error_handlers(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.chat import chat_bp
    from routes.health import health_bp
    from routes.api_routes import api_bp
    from routes.view_routes import view_bp
    from services.session_service import SessionService

    app.register_blueprint(auth_bp)
    # app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp(adk_service, session_service))
    app.register_blueprint(view_bp())
    app.register_blueprint(health_bp)

    # Log initialization
    print(f"\n{'='*70}")
    print(f"Flask App Initialized")
    print(f"Configuration: {config_name}")
    print(f"Debug Mode: {app.debug}")
    print(f"Azure Tenant ID: {app.config.get('AZURE_TENANT_ID')}")
    print(f"Azure Client ID: {app.config.get('AZURE_CLIENT_ID')}")
    print(f"Azure Scopes: {app.config.get('AZURE_SCOPES')}")
    print(f"Redirect URI: {app.config.get('REDIRECT_URI')}")
    print(f"Client Secret Set: {bool(app.config.get('AZURE_CLIENT_SECRET'))}")
    print(f"ADK API: {app.config.get('ADK_API', 'http://localhost:8000')}")
    print(f"{'='*70}\n")

    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)