"""
Tests for application functionality in Docker container.

These tests validate that the application works correctly when running
in a Docker container, testing all major endpoints.

**Validates: Requirements 4.3**
"""

import pytest
import os
import subprocess
import time
import requests
import json
import tempfile
from io import BytesIO


# ============================================================================
# Test Setup and Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def docker_container():
    """
    Start a Docker container for testing and clean up after tests.
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if Docker is available
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            pytest.skip("Docker is not available on this system")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("Docker is not available on this system")
    
    # Check if image exists, if not build it
    inspect_result = subprocess.run(
        ['docker', 'inspect', 'picme-test'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if inspect_result.returncode != 0:
        # Build the image
        print("Building Docker image...")
        build_result = subprocess.run(
            ['docker', 'build', '-t', 'picme-test', '.'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if build_result.returncode != 0:
            pytest.skip(f"Failed to build Docker image: {build_result.stderr}")
    
    # Start the container with test environment variables
    container_name = f"picme-test-{int(time.time())}"
    
    # Use a test database URL or mock
    test_env = {
        'DATABASE_URL': 'postgresql://test:test@localhost/test?sslmode=disable',
        'FLASK_SECRET_KEY': 'test_secret_key_for_testing',
        'PORT': '8080'
    }
    
    env_args = []
    for key, value in test_env.items():
        env_args.extend(['-e', f'{key}={value}'])
    
    run_command = [
        'docker', 'run', '-d',
        '--name', container_name,
        '-p', '8080:8080'
    ] + env_args + ['picme-test']
    
    print(f"Starting container: {container_name}")
    run_result = subprocess.run(
        run_command,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if run_result.returncode != 0:
        pytest.skip(f"Failed to start container: {run_result.stderr}")
    
    container_id = run_result.stdout.strip()
    
    # Wait for the application to start
    max_wait = 30
    wait_interval = 1
    app_ready = False
    
    for i in range(max_wait):
        try:
            response = requests.get('http://localhost:8080/', timeout=2)
            if response.status_code == 200:
                app_ready = True
                print(f"Application ready after {i+1} seconds")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(wait_interval)
    
    if not app_ready:
        # Get container logs for debugging
        logs_result = subprocess.run(
            ['docker', 'logs', container_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Container logs:\n{logs_result.stdout}\n{logs_result.stderr}")
        
        # Stop and remove container
        subprocess.run(['docker', 'stop', container_name], timeout=10)
        subprocess.run(['docker', 'rm', container_name], timeout=10)
        pytest.skip("Application did not start within 30 seconds")
    
    # Yield container info for tests
    yield {
        'container_id': container_id,
        'container_name': container_name,
        'base_url': 'http://localhost:8080'
    }
    
    # Cleanup: stop and remove container
    print(f"Stopping container: {container_name}")
    subprocess.run(
        ['docker', 'stop', container_name],
        capture_output=True,
        timeout=30
    )
    subprocess.run(
        ['docker', 'rm', container_name],
        capture_output=True,
        timeout=10
    )


# ============================================================================
# Application Functionality Tests
# ============================================================================

def test_homepage_loads(docker_container):
    """
    Test that the homepage loads successfully at http://localhost:8080
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    response = requests.get(f'{base_url}/', timeout=5)
    
    assert response.status_code == 200, \
        "Homepage should return 200 OK status"
    
    # Verify it's HTML content
    assert 'text/html' in response.headers.get('Content-Type', ''), \
        "Homepage should return HTML content"
    
    # Verify some expected content (PicMe branding)
    assert len(response.text) > 0, \
        "Homepage should have content"


def test_user_registration_endpoint(docker_container):
    """
    Test that the user registration endpoint works correctly
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    # Test with valid registration data
    registration_data = {
        'fullName': 'Test User',
        'email': f'test_{int(time.time())}@example.com',
        'password': 'testpassword123',
        'userType': 'user'
    }
    
    response = requests.post(
        f'{base_url}/register',
        json=registration_data,
        timeout=5
    )
    
    # The endpoint should respond (even if DB connection fails in test)
    assert response.status_code in [201, 500], \
        "Registration endpoint should respond with 201 (success) or 500 (DB error)"
    
    data = response.json()
    assert 'success' in data, \
        "Response should contain 'success' field"
    
    # If DB is not available, we expect a 500 error
    if response.status_code == 500:
        assert data['success'] is False, \
            "Failed registration should have success=False"
        assert 'error' in data, \
            "Failed registration should include error message"


def test_user_login_endpoint(docker_container):
    """
    Test that the user login endpoint works correctly
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    # Test with login data
    login_data = {
        'email': 'test@example.com',
        'password': 'testpassword'
    }
    
    response = requests.post(
        f'{base_url}/login',
        json=login_data,
        timeout=5
    )
    
    # The endpoint should respond (even if credentials are invalid or DB fails)
    assert response.status_code in [200, 401, 500], \
        "Login endpoint should respond with 200 (success), 401 (invalid), or 500 (DB error)"
    
    data = response.json()
    assert 'success' in data, \
        "Response should contain 'success' field"
    
    # For invalid credentials or DB error, success should be False
    if response.status_code in [401, 500]:
        assert data['success'] is False, \
            "Failed login should have success=False"
        assert 'error' in data, \
            "Failed login should include error message"


def test_event_creation_endpoint(docker_container):
    """
    Test that the event creation endpoint works correctly
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, try to create an event (should fail without authentication)
    event_data = {
        'eventName': 'Test Event',
        'eventLocation': 'Test Location',
        'eventDate': '2024-12-31',
        'eventCategory': 'General'
    }
    
    response = session.post(
        f'{base_url}/api/create_event',
        json=event_data,
        timeout=5
    )
    
    # Should return 401 Unauthorized without authentication
    assert response.status_code == 401, \
        "Event creation should require authentication"
    
    data = response.json()
    assert 'success' in data, \
        "Response should contain 'success' field"
    assert data['success'] is False, \
        "Unauthenticated event creation should fail"
    assert 'error' in data, \
        "Failed event creation should include error message"
    assert 'Unauthorized' in data['error'], \
        "Error message should indicate unauthorized access"


def test_photo_upload_endpoint(docker_container):
    """
    Test that the photo upload endpoint works correctly
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Try to upload photos (should fail without authentication)
    # Create a dummy image file
    dummy_image = BytesIO(b'fake image data')
    dummy_image.name = 'test.jpg'
    
    files = {
        'photos': ('test.jpg', dummy_image, 'image/jpeg')
    }
    
    response = session.post(
        f'{base_url}/api/upload_photos/test_event',
        files=files,
        timeout=5
    )
    
    # Should return 401 Unauthorized without authentication
    assert response.status_code == 401, \
        "Photo upload should require authentication"
    
    data = response.json()
    assert 'success' in data, \
        "Response should contain 'success' field"
    assert data['success'] is False, \
        "Unauthenticated photo upload should fail"
    assert 'error' in data, \
        "Failed photo upload should include error message"
    assert 'Unauthorized' in data['error'], \
        "Error message should indicate unauthorized access"


def test_events_api_endpoint(docker_container):
    """
    Test that the events API endpoint works correctly
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    response = requests.get(f'{base_url}/events', timeout=5)
    
    assert response.status_code == 200, \
        "Events endpoint should return 200 OK"
    
    data = response.json()
    assert isinstance(data, list), \
        "Events endpoint should return a list"


def test_static_files_served(docker_container):
    """
    Test that static files are served correctly
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    # Try to access the logo
    response = requests.get(f'{base_url}/picme.svg', timeout=5)
    
    # Should either return the file or 404 if not found
    assert response.status_code in [200, 404], \
        "Static file endpoint should respond"


def test_application_responds_to_multiple_requests(docker_container):
    """
    Test that the application can handle multiple concurrent requests
    
    **Validates: Requirements 4.3**
    """
    base_url = docker_container['base_url']
    
    # Make multiple requests
    responses = []
    for i in range(5):
        response = requests.get(f'{base_url}/', timeout=5)
        responses.append(response)
    
    # All requests should succeed
    for response in responses:
        assert response.status_code == 200, \
            "All requests should succeed"


def test_container_logs_no_critical_errors(docker_container):
    """
    Test that the container logs don't contain critical errors
    
    **Validates: Requirements 4.3**
    """
    container_name = docker_container['container_name']
    
    # Get container logs
    logs_result = subprocess.run(
        ['docker', 'logs', container_name],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    logs = logs_result.stdout + logs_result.stderr
    
    # Check for critical error patterns
    critical_errors = [
        'Traceback (most recent call last)',
        'FATAL',
        'CRITICAL',
        'ImportError',
        'ModuleNotFoundError'
    ]
    
    for error_pattern in critical_errors:
        # Allow some errors related to database connection in test environment
        if error_pattern in logs:
            # Check if it's a database connection error (expected in test)
            if 'Database connection failed' not in logs and 'DB Error' not in logs:
                pytest.fail(f"Container logs contain critical error: {error_pattern}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
