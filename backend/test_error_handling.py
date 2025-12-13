"""
Test error handling for download page APIs
"""
import pytest
import json
import os
import tempfile
from app import app, EVENTS_DATA_PATH

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client

@pytest.fixture
def authenticated_session(client):
    """Create an authenticated session"""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_email'] = 'test@example.com'
        sess['person_id'] = 'test_person_123'
    return client

def test_user_photos_no_person_id(client):
    """Test user_photos API returns error when no person_id in session"""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_email'] = 'test@example.com'
        # No person_id set
    
    response = client.get('/api/user_photos')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error_code' in data
    assert data['error_code'] == 'NO_PERSON_ID'

def test_user_photos_empty_processed_folder(authenticated_session):
    """Test user_photos API handles missing processed folder gracefully"""
    # Set the processed folder to a nonexistent path
    original_folder = app.config['PROCESSED_FOLDER']
    app.config['PROCESSED_FOLDER'] = '/nonexistent/path'
    
    try:
        response = authenticated_session.get('/api/user_photos')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['events'] == []
        assert data['total_photos'] == 0
    finally:
        # Restore original folder
        app.config['PROCESSED_FOLDER'] = original_folder

def test_download_photos_missing_parameters(authenticated_session):
    """Test download_photos API validates required parameters"""
    response = authenticated_session.post('/api/download_photos',
                                         json={},
                                         content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error_code' in data
    # Empty JSON object {} is falsy, so it triggers INVALID_REQUEST
    assert data['error_code'] == 'INVALID_REQUEST'

def test_download_photos_invalid_request(authenticated_session):
    """Test download_photos API handles invalid JSON"""
    response = authenticated_session.post('/api/download_photos',
                                         data='invalid json',
                                         content_type='application/json')
    # Invalid JSON causes an exception that's caught by the outer handler, returning 500
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error_code' in data
    assert data['error_code'] == 'INTERNAL_ERROR'

def test_download_photos_too_many_photos(authenticated_session):
    """Test download_photos API enforces photo limit"""
    # Create request with more than 500 photos
    photos = [{'filename': f'photo_{i}.jpg', 'photoType': 'individual'} for i in range(501)]
    
    response = authenticated_session.post('/api/download_photos',
                                         json={
                                             'event_id': 'test_event',
                                             'person_id': 'test_person',
                                             'photos': photos
                                         },
                                         content_type='application/json')
    assert response.status_code == 413
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error_code' in data
    assert data['error_code'] == 'TOO_MANY_PHOTOS'

def test_download_photos_no_photos_found(authenticated_session, tmp_path):
    """Test download_photos API handles case when no photos exist"""
    # Set up temporary processed folder
    app.config['PROCESSED_FOLDER'] = str(tmp_path)
    
    response = authenticated_session.post('/api/download_photos',
                                         json={
                                             'event_id': 'nonexistent_event',
                                             'person_id': 'nonexistent_person',
                                             'photos': [
                                                 {'filename': 'photo1.jpg', 'photoType': 'individual'}
                                             ]
                                         },
                                         content_type='application/json')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error_code' in data
    assert data['error_code'] == 'NO_PHOTOS_FOUND'

def test_download_photos_invalid_photos_format(authenticated_session):
    """Test download_photos API validates photos parameter is a list"""
    response = authenticated_session.post('/api/download_photos',
                                         json={
                                             'event_id': 'test_event',
                                             'person_id': 'test_person',
                                             'photos': 'not_a_list'
                                         },
                                         content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error_code' in data
    assert data['error_code'] == 'INVALID_PHOTOS_FORMAT'

def test_download_photos_empty_photos_list(authenticated_session):
    """Test download_photos API handles empty photos list"""
    response = authenticated_session.post('/api/download_photos',
                                         json={
                                             'event_id': 'test_event',
                                             'person_id': 'test_person',
                                             'photos': []
                                         },
                                         content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error_code' in data
    # Empty list is treated as missing parameter due to Python's falsy behavior
    assert data['error_code'] == 'MISSING_PARAMETERS'

def test_user_photos_session_expired(client):
    """Test user_photos API handles expired session"""
    # No session data at all
    response = client.get('/api/user_photos')
    # Should redirect to login (302) or return 401
    assert response.status_code in [302, 401]

def test_download_photos_session_expired(client):
    """Test download_photos API handles expired session"""
    # No session data at all
    response = client.post('/api/download_photos',
                          json={
                              'event_id': 'test_event',
                              'person_id': 'test_person',
                              'photos': [{'filename': 'photo1.jpg', 'photoType': 'individual'}]
                          },
                          content_type='application/json')
    # Should redirect to login (302) or return 401
    assert response.status_code in [302, 401]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
