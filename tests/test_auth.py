# Testar inloggningssidan
def test_login_page(client):
    """Testar att inloggningssidan laddas korrekt"""
    response = client.get('/login')
    assert response.status_code == 200 # Kollar efter statuskod 200
    assert b'Sign In' in response.data  # Kollar efter "Sign In" i responsen
    assert b"Don't have an account?" in response.data # Kollar efter "Don't have an account?" i responsen

# Testar inloggning med korrekta uppgifter
def test_valid_login(client, test_user):
    """Testar inloggning med giltiga inloggningsuppgifter"""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert b'Dashboard' in response.data  # Kollar efter "Dashboard" i responsen

# Testar inloggning med felaktiga uppgifter
def test_invalid_login(client):
    """Testar inloggning med ogiltiga inloggningsuppgifter"""
    response = client.post('/login', data={
        'username': 'wronguser', # Fel användarnamn som inte finns
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert b'Invalid username or password' in response.data # Kollar efter "Invalid username or password" i responsen

# Testar användarregistrering
def test_register(client):
    """Testar registrering av ny användare"""
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)
    assert b'Registration successful' in response.data # Kollar efter "Registration successful" i responsen

# Testar användarregistrering med uppgifter som redan finns
def test_duplicate_register(client, test_user):
    """Testar registrering med användarnamn som redan finns"""
    response = client.post('/register', data={
        'username': 'testuser',  # Använder befintligt användarnamn
        'email': 'another@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)
    assert b'Username already exists' in response.data # Kollar efter "Username already exists" i responsen

# Kan inte testa invalid register för det går inte att trycka på "Create Account" om inte alla 
# Krav uppfylls