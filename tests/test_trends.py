from app import db

# Testar trendanalysen
def test_trends_page(auth_client, app):
    """Testar att trendanalysen laddas korrekt"""
    with app.app_context():
        with auth_client.session_transaction() as session:
            session['_fresh'] = True
        response = auth_client.get('/trends')
        assert response.status_code == 200
        assert b'trends-container' in response.data  # Kollar efter "trends-container" i responsen
        assert b'keyword-input' in response.data     # Kollar efter "keyword-input" i responsen

# Testar analys av trender
def test_analyze_trends(auth_client, app):
    """Testar att analysera trender"""
    with app.app_context():
        with auth_client.session_transaction() as session:
            session['_fresh'] = True
        response = auth_client.post('/analyze_trends', 
            json={'keywords': ['python', 'flask']},
            follow_redirects=True
        )
        assert response.status_code == 200 # Kollar efter statuskod 200
        assert 'trends' in response.json # Kollar efter att det finns 'trends' i responsen

# Testar nyhetssummeringar
def test_summarize_news(auth_client, app):
    """Testar att summera nyheter"""
    with app.app_context():
        try:
            with auth_client.session_transaction() as session:
                session['_fresh'] = True
            response = auth_client.post('/summarize_news',
                json={'keyword': 'technology'},
                follow_redirects=True
            )
            assert response.status_code == 200 # Kollar efter statuskod 200
            assert 'summary' in response.json # Kollar efter att det finns 'summary' i responsen
        finally:
            # Stänger anslutningen till databasen
            db.session.remove()