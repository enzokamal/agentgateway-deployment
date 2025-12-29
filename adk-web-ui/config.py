import os

class Config:
    ADK_API = os.getenv("ADK_API", "http://localhost:8000")
    APP_NAME = os.getenv("ADK_APP_NAME", "my_sample_agent")
    USER_ID = os.getenv("ADK_USER_ID", "u_123")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret")
