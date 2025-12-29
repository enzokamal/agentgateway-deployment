from flask import Flask
from flask_session import Session

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize Flask-Session
    Session(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app
