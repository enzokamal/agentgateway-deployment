from flask import Flask, session
from flask_session import Session
import os

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Ensure session directory exists
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Initialize session
    Session(app)
    
    # Register blueprints
    from app.routes import bp as main_bp, adk_chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(adk_chat_bp)
    
    # Debug logging
    @app.before_request
    def log_request_info():
        from flask import request
        if app.debug:
            print(f"\n{'='*70}")
            print(f"REQUEST: {request.method} {request.path}")
            print(f"Endpoint: {request.endpoint}")
            print(f"Session authenticated: {session.get('authenticated', False)}")
            print(f"{'='*70}\n")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(e):
        print(f"Internal error: {str(e)}")
        return {'error': 'Internal server error'}, 500
    
    print(f"\n{'='*70}")
    print(f"Flask App Initialized")
    print(f"Configuration: {config_name}")
    print(f"Debug Mode: {app.debug}")
    print(f"Azure Tenant ID: {app.config.get('AZURE_TENANT_ID')}")
    print(f"Azure Client ID: {app.config.get('AZURE_CLIENT_ID')}")
    print(f"Azure Scopes: {app.config.get('AZURE_SCOPES')}")
    print(f"Redirect URI: {app.config.get('REDIRECT_URI')}")
    print(f"Client Secret Set: {bool(app.config.get('AZURE_CLIENT_SECRET'))}")
    print(f"{'='*70}\n")
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)