import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Default to production database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 
                                      f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'project55.db')}")
    
    # Test configuration - automatically use test db when FLASK_TESTING is set
    if os.getenv('FLASK_TESTING'):
        # Använder in-memory database för tests
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
