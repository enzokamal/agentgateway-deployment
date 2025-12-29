import os

class Config:
    ADK_API = os.getenv("ADK_API", "http://localhost:8000")
    APP_NAME = os.getenv("ADK_APP_NAME", "my_sample_agent")
    USER_ID = os.getenv("ADK_USER_ID", "u_123")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret")
    SESSION_TYPE = 'filesystem'

    # Entra ID Configuration
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "11ddc0cd-e6fc-48b6-8832-de61800fb41e")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "6ba231bb-ad9e-41b9-b23d-674c80196bbd")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
    REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/auth/callback")
