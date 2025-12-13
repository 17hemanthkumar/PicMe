"""
Unit tests for the /api/user_photos endpoint.

These tests validate that the endpoint correctly fetches and aggregates
user photos across all events.
"""

import pytest
import os
import json
import tempfile
import shutil
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    
    # Create temporary directories
    temp_upload_folder = tempfile.mkdtemp()
    temp_processed_folder = tempfile.mkdtemp()
    temp_events_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    
    # Store original paths
    original_upload_folder = app.config.get('UPLOAD_FOLDER')
    original_processed_folder = app.config.get('PROCESSED_FOLDER')
    
    # Override paths
    app.config['UPLOAD_FOLDER'] = temp_upload_folder
    app.config['PROCESSED_FOLDER'] = temp_processed_folder
    
    import app as app_module
    original_events_path = app_module.EVENTS_DATA_PATH
    app_module.EVENTS_DATA_PATH = temp_events_file.name
    
    # Create test events data
    test_events = [
        {
            "id": "event_test1",
            "name": "Test Event 1",
            "location": "Test Location 1",
            "date": "2024-12-25",
            "category": "Festival"
        },
        {
            "id": "event_test2",
            "name": "Test Event 2",
            "location": "Test Location 2",
            "date": "2024-11-15",
            "category": "Corporate"
        }
    ]
    
    with open(temp_events_file.name, 'w') as f:
        json.dump(test_events, f)
    
    with app.test_client() as client:
        yield client
    
    # Cleanup
    try:
        shutil.rmtree(temp_upload_folder)
        shutil.rmtree(temp_processed_folder)
        os.unlink(temp_events_file.name)
    except:
        pass
    
    # Restore original paths
    app.config['UPLOAD_FOLDER'] = original_upload_folder
    app.config['PROCESSED_FOLDER'] = original_processed_folder
    app_module.EVENTS_DATA_PATH = original_events_path


def create_test_photo_structure(processed_folder, event_id, person_id, individual_photos=None, group_photos=None):
    """Helper function to create test photo directory structure"""
    person_dir = os.path.join(processed_folder, event_id, person_id)
    individual_dir = os.path.join(person_dir, "individual")
    group_dir = os.path.join(person_dir, "group")
    
    os.makedirs(individual_dir, exist_ok=True)
    os.makedirs(group_dir, exist_ok=True)
    
    # Create dummy photo files
    if individual_photos:
        for photo in individual_photos:
            photo_path = os.path.join(individual_dir, photo)
            with open(photo_path, 'w') as f:
                f.write('dummy photo content')
    
    if group_photos:
        for photo in group_photos:
            photo_path = os.path.join(group_dir, photo)
            with open(photo_path, 'w') as f:
                f.write('dummy photo content')


def test_user_photos_requires_authentication(client):
    """Test that /api/user_photos requires authentication"""
    response = client.get('/api/user_photos')
    
    # Should redirect to login page
    assert response.status_code == 302
    assert '/login' in response.location


def test_user_photos_no_person_id_in_session(client):
    """Test that endpoint returns error when person_id is not in session"""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 1
        sess['user_email'] = 'test@example.com'
        # No person_id set
    
    response = client.get('/api/user_photos')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'person_id' in data['error'].lower()


def test_user_photos_returns_empty_when_no_photos(client):
    """Test that endpoint returns empty list when user has no photos"""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 1
        sess['user_email'] = 'test@example.com'
        sess['person_id'] = 'person_0001'
    
    response = client.get('/api/user_photos')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['events'] == []
    assert data['total_photos'] == 0


def test_user_photos_returns_photos_from_single_event(client):
    """Test that endpoint correctly returns photos from a single event"""
    person_id = 'person_0001'
    
    # Create test photo structure
    create_test_photo_structure(
        app.config['PROCESSED_FOLDER'],
        'event_test1',
        person_id,
        individual_photos=['photo1.jpg', 'photo2.jpg'],
        group_photos=['watermarked_photo3.jpg']
    )
    
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 1
        sess['user_email'] = 'test@example.com'
        sess['person_id'] = person_id
    
    response = client.get('/api/user_photos')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['events']) == 1
    assert data['total_photos'] == 3
    
    event = data['events'][0]
    assert event['event_id'] == 'event_test1'
    assert event['event_name'] == 'Test Event 1'
    assert event['person_id'] == person_id
    assert len(event['individual_photos']) == 2
    assert len(event['group_photos']) == 1
    assert event['photo_count'] == 3


def test_user_photos_returns_photos_from_multiple_events(client):
    """Test that endpoint correctly aggregates photos from multiple events"""
    person_id = 'person_0001'
    
    # Create test photo structure for multiple events
    create_test_photo_structure(
        app.config['PROCESSED_FOLDER'],
        'event_test1',
        person_id,
        individual_photos=['photo1.jpg'],
        group_photos=['watermarked_photo2.jpg', 'watermarked_photo3.jpg']
    )
    
    create_test_photo_structure(
        app.config['PROCESSED_FOLDER'],
        'event_test2',
        person_id,
        individual_photos=['photo4.jpg', 'photo5.jpg'],
        group_photos=['watermarked_photo6.jpg']
    )
    
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 1
        sess['user_email'] = 'test@example.com'
        sess['person_id'] = person_id
    
    response = client.get('/api/user_photos')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['events']) == 2
    assert data['total_photos'] == 6
    
    # Verify events are sorted by date (most recent first)
    assert data['events'][0]['event_date'] == '2024-12-25'  # event_test1
    assert data['events'][1]['event_date'] == '2024-11-15'  # event_test2


def test_user_photos_only_returns_user_photos(client):
    """Test that endpoint only returns photos for the authenticated user"""
    person_id = 'person_0001'
    other_person_id = 'person_0002'
    
    # Create photos for authenticated user
    create_test_photo_structure(
        app.config['PROCESSED_FOLDER'],
        'event_test1',
        person_id,
        individual_photos=['photo1.jpg']
    )
    
    # Create photos for another user (should not be returned)
    create_test_photo_structure(
        app.config['PROCESSED_FOLDER'],
        'event_test1',
        other_person_id,
        individual_photos=['photo2.jpg', 'photo3.jpg']
    )
    
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 1
        sess['user_email'] = 'test@example.com'
        sess['person_id'] = person_id
    
    response = client.get('/api/user_photos')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['events']) == 1
    assert data['total_photos'] == 1
    assert data['events'][0]['person_id'] == person_id


def test_user_photos_includes_correct_photo_urls(client):
    """Test that photo URLs are correctly formatted"""
    person_id = 'person_0001'
    
    create_test_photo_structure(
        app.config['PROCESSED_FOLDER'],
        'event_test1',
        person_id,
        individual_photos=['photo1.jpg'],
        group_photos=['watermarked_photo2.jpg']
    )
    
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = 1
        sess['user_email'] = 'test@example.com'
        sess['person_id'] = person_id
    
    response = client.get('/api/user_photos')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    event = data['events'][0]
    
    # Verify individual photo URL format
    assert event['individual_photos'][0]['url'] == f"/photos/event_test1/{person_id}/individual/photo1.jpg"
    assert event['individual_photos'][0]['filename'] == 'photo1.jpg'
    
    # Verify group photo URL format
    assert event['group_photos'][0]['url'] == f"/photos/event_test1/{person_id}/group/watermarked_photo2.jpg"
    assert event['group_photos'][0]['filename'] == 'watermarked_photo2.jpg'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
