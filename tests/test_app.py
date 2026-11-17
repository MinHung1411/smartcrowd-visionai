import pytest
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from app import create_app, db
from app.models.user import User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_login_page_renders(client):
    """Verify that login page renders with HTTP 200"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'SmartCrowd' in response.data

def test_demo_prefilled_login(client):
    """Verify demo login succeeds and redirects to dashboard"""
    response = client.post('/auth/login', data={'email': 'demo', 'password': 'demo123'}, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/dashboard'

def test_logout(client):
    """Verify clean logout workflow"""
    client.post('/auth/login', data={'email': 'demo', 'password': 'demo123'})
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/auth/login'
