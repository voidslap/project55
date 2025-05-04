from app.models import Chat
from app import db

# Testar att chatsidan laddas
def test_chat_page(auth_client):
    """Testar att chatsidan laddas korrekt"""
    response = auth_client.get('/chat')
    assert response.status_code == 200
    assert b'Type your message' in response.data # Förväntar sig "Type your message" i responsen

# Testar att skicka meddelande
def test_send_message(auth_client):
    """Testar att skicka ett meddelande och få svar"""
    response = auth_client.post('/chat', 
        json={'message': 'Hello'},
        follow_redirects=True
    )
    assert response.status_code == 200 # Förväntar sig statuskod 200
    assert 'response' in response.json # Förväntar sig att det finns ett svar i responsen

# Testar chathistorik
def test_chat_history(auth_client, app, test_user):
    """Testar sidan för chathistorik"""
    with app.app_context():
        # Skapar en ny chat för test
        chat = Chat(
            user_id=test_user.id,
            title="Test Chat"
        )
        db.session.add(chat)
        db.session.commit()
        
        # Testar endpoints
        response = auth_client.get('/chat_history')
        assert response.status_code == 200 # Förväntar sig statuskod 200
        assert b'Test Chat' in response.data # Förväntar sig "Test Chat" i responsen
        
        # Städar upp efter testet
        db.session.delete(chat)
        db.session.commit()