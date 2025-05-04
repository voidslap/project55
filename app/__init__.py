from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import logging
import os

# Skapar en instans av SQLAlchemy och LoginManager
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app(test_config=None):
    """Application factory with optional test configuration"""
    app = Flask(__name__)
    
    # Skapar instance folder om den inte finns
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Load config - antingen test config eller default Config class
    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)

    # Configure logging
    app.logger.setLevel(logging.INFO)

    with app.app_context():
        from .routes import bp
        app.register_blueprint(bp)
        
        # Only create tables if not testing (tests handle their own DB)
        if not app.config.get('TESTING'):
            from . import models
            db.create_all()

    return app