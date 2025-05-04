# Testar inställningssidan
def test_settings_page(auth_client):
    """Testar att inställningssidan laddas korrekt"""
    response = auth_client.get('/settings')
    assert response.status_code == 200 # Kollar efter statuskod 200
    assert b'Company Settings' in response.data # Kollar efter "Company Settings" i responsen

# Testar att spara företagsinställningar
def test_save_settings(auth_client, app, test_user):
    """Testar att spara företagsinställningar"""
    with app.app_context():
        response = auth_client.post('/settings', data={
            'company_name': 'Updated Company',
            'industry': 'technology',
            'background': 'Updated background',
            'target_audience': 'Updated audience',
            'brand_voice': 'professional',
            'key_values': 'Innovation, Quality'
        }, follow_redirects=True)
        assert response.status_code == 200 # Kollar efter statuskod 200
        assert b'Company settings updated successfully' in response.data # Kollar efter "Company settings updated successfully" i responsen