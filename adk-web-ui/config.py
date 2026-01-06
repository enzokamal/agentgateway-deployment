import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # ADK API Configuration
    ADK_API = os.getenv("ADK_API")
    APP_NAME = os.getenv("ADK_APP_NAME")
    USER_ID = os.getenv("ADK_USER_ID")

    # Flask Session Configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.getenv("SESSION_FILE_DIR")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # Azure Entra ID (Azure AD) OAuth Configuration
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")

    # Include 'openid' scope for getting ID tokens with user info
    # Combined with the custom API scope
    AZURE_SCOPES = os.getenv("AZURE_SCOPES")

    REDIRECT_URI = os.getenv("REDIRECT_URI")

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}