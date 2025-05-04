import os
import shutil
import pytest
import time
from app import create_app, db
from app.models import User, Company, Chat, Message
from werkzeug.security import generate_password_hash
from flask_login import login_user

def pytest_configure(config):
    """Sätter upp testmiljön innan några tester körs"""
    os.environ['FLASK_TESTING'] = 'true'
    print("\nTest environment enabled")

def pytest_unconfigure(config):
    """Städar upp test miljön efter att alla tester är klara"""
    os.environ.pop('FLASK_TESTING', None)
    print("\nTest environment cleaned up")

@pytest.fixture(scope='session')
def app():
    """Skapar en test app med in-memory databas"""
    test_config = {
        "TESTING": True,
        "DEBUG": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Använder in-memory databas istället för den riktiga databasen
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key",
        "ANTHROPIC_API_KEY": "test_key",
        "RATELIMIT_ENABLED": False,
        "LOGIN_DISABLED": False,
        "SERVER_NAME": "localhost.localdomain",
        "APPLICATION_ROOT": "/",
        "PREFERRED_URL_SCHEME": "http",
        "TRUSTED_HOSTS": ["localhost.localdomain"],
        "PROPAGATE_EXCEPTIONS": True,
        "SECRET_KEY_FALLBACKS": [],
        "SESSION_COOKIE_SECURE": False,
        "SESSION_COOKIE_DOMAIN": False,
        "SESSION_COOKIE_NAME": "session",
        "SESSION_COOKIE_PATH": "/",
        "SESSION_COOKIE_PARTITIONED": False,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "TEMPLATES_AUTO_RELOAD": True,
        "MAX_FORM_MEMORY_SIZE": 16 * 1024 * 1024,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
        "MAX_FORM_PARTS": 1000,
        "PERMANENT_SESSION_LIFETIME": 3600,
        "EXPLAIN_TEMPLATE_LOADING": False
    }
    
    app = create_app(test_config)
    
    # Skapar tabeller i in-memory databasen
    with app.app_context():
        db.create_all()
        yield app

        # Cleanup
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Skapar en testklient."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Skapar en test runner."""
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Skapar en testanvändare."""
    with app.app_context():
        User.query.filter_by(username='testuser').delete()
        db.session.commit()
        user = User(
            username='testuser',
            email='test@example.com',
            hashed_password=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        yield user
        db.session.rollback()
        User.query.filter_by(username='testuser').delete()
        db.session.commit()

@pytest.fixture
def auth_client(app, client, test_user):
    """Skapar en autentiserad klient för tester."""
    with app.test_request_context():
        with app.app_context():
            user = db.session.get(User, test_user.id)
            login_user(user)
        with client.session_transaction() as session:
            session['_fresh'] = True
            session['_user_id'] = str(user.id)
        response = client.get('/dashboard')
        if response.status_code != 200:
            raise AssertionError(f"Inloggningen misslyckades: {response.status_code}")
        return client

@pytest.fixture
def test_company(app, test_user):
    """Skapar ett testföretag."""
    with app.app_context():
        company = Company(
            user_id=test_user.id,
            company_name='Test Company',
            industry='technology',
            background='Test background',
            target_audience='Test audience',
            brand_voice='professional'
        )
        db.session.add(company)
        db.session.commit()
        return company