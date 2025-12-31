import os

class Config:
    # ADK API Configuration
    ADK_API = os.getenv("ADK_API", "http://adk-agent-service.agentgateway-system.svc.cluster.local:8070")
    APP_NAME = os.getenv("ADK_APP_NAME", "my_sample_agent")
    USER_ID = os.getenv("ADK_USER_ID", "u_123")
    
    # Flask Session Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_change_in_production")
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.getenv("SESSION_FILE_DIR", "/tmp/flask_session")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # Azure Entra ID (Azure AD) OAuth Configuration
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "11ddc0cd-e6fc-48b6-8832-de61800fb41e")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "6ba231bb-ad9e-41b9-b23d-674c80196bbd")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")  # Leave empty for public client
    
    # Include 'openid' scope for getting ID tokens with user info
    # Combined with the custom API scope
    AZURE_SCOPES = os.getenv(
        "AZURE_SCOPES",
        "openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access"
    )
    
    REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/auth/callback")

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # In production, these should come from environment variables
    SECRET_KEY = os.getenv("SECRET_KEY")  # Must be set in production
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")  # Must be set in production
    REDIRECT_URI = os.getenv("REDIRECT_URI")  # Should be your production URL

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}