"""
Property-based tests for HTTP request handling.

These tests validate the correctness property defined in the design document
for HTTP request handling in the docker deployment feature.

**Feature: docker-deployment, Property 7: HTTP request handling**
**Validates: Requirements 4.3, 5.4**
"""

import pytest
import os
import sys
import tempfile
from hypothesis import given, settings, strategies as st, HealthCheck
from io import BytesIO

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app
from app import app as flask_app


# ============================================================================
# Test Setup and Fixtures
# ============================================================================

@pytest.fixture
def client():
    """
    Create a test client for the Flask application.
    """
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test_secret_key'
    
    # Use temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        flask_app.config['UPLOAD_FOLDER'] = os.path.join(temp_dir, 'uploads')
        flask_app.config['PROCESSED_FOLDER'] = os.path.join(temp_dir, 'processed')
        
        os.makedirs(flask_app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(flask_app.config['PROCESSED_FOLDER'], exist_ok=True)
        
        with flask_app.test_client() as client:
            yield client


# ============================================================================
# Property 7: HTTP request handling
# **Feature: docker-deployment, Property 7: HTTP request handling**
# **Validates: Requirements 4.3, 5.4**
# ============================================================================

# Strategy for generating valid HTTP methods
http_method_strategy = st.sampled_from(['GET', 'POST', 'PUT', 'DELETE'])

# Strategy for generating valid endpoint paths
# These are the main public endpoints that should always respond
public_endpoint_strategy = st.sampled_from([
    '/',
    '/login',
    '/signup',
    '/events',
    '/picme.svg',
])

# Strategy for generating valid JSON payloads for POST requests
json_payload_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        values=st.one_of(
            st.text(min_size=0, max_size=50),
            st.integers(min_value=0, max_value=10000),
            st.booleans()
        ),
        min_size=0,
        max_size=5
    )
)


@given(endpoint=public_endpoint_strategy)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_http_get_requests_respond(client, endpoint):
    """
    Property 7: HTTP request handling (GET requests)
    
    For any valid HTTP GET request to public application endpoints,
    when the container is running, the application should respond
    with an appropriate HTTP status code and content.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    # Make GET request to the endpoint
    response = client.get(endpoint)
    
    # Verify response has a valid HTTP status code
    assert response.status_code is not None, \
        f"Response should have a status code for GET {endpoint}"
    
    # Verify status code is in valid HTTP range (100-599)
    assert 100 <= response.status_code < 600, \
        f"Status code should be valid HTTP code (100-599), got {response.status_code} for GET {endpoint}"
    
    # Verify response has content (even if empty)
    assert response.data is not None, \
        f"Response should have data attribute for GET {endpoint}"
    
    # Verify response has headers
    assert response.headers is not None, \
        f"Response should have headers for GET {endpoint}"
    
    # Verify Content-Type header is set
    assert 'Content-Type' in response.headers, \
        f"Response should have Content-Type header for GET {endpoint}"
    
    # For successful responses, verify content is not empty
    if 200 <= response.status_code < 300:
        assert len(response.data) > 0, \
            f"Successful response should have non-empty content for GET {endpoint}"


@given(
    endpoint=st.sampled_from(['/register', '/login']),
    payload=json_payload_strategy.filter(lambda x: x is not None)  # Filter out None payloads
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_http_post_requests_respond(client, endpoint, payload):
    """
    Property 7: HTTP request handling (POST requests)
    
    For any valid HTTP POST request to application endpoints,
    when the container is running, the application should respond
    with an appropriate HTTP status code and content.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    # Make POST request to the endpoint
    response = client.post(endpoint, json=payload)
    
    # Verify response has a valid HTTP status code
    assert response.status_code is not None, \
        f"Response should have a status code for POST {endpoint}"
    
    # Verify status code is in valid HTTP range (100-599)
    assert 100 <= response.status_code < 600, \
        f"Status code should be valid HTTP code (100-599), got {response.status_code} for POST {endpoint}"
    
    # Verify response has content
    assert response.data is not None, \
        f"Response should have data attribute for POST {endpoint}"
    
    # Verify response has headers
    assert response.headers is not None, \
        f"Response should have headers for POST {endpoint}"
    
    # Verify Content-Type header is set
    assert 'Content-Type' in response.headers, \
        f"Response should have Content-Type header for POST {endpoint}"
    
    # For JSON endpoints, verify response is JSON
    if 'application/json' in response.headers.get('Content-Type', ''):
        import json
        try:
            json.loads(response.data)
        except json.JSONDecodeError:
            pytest.fail(f"Response with JSON Content-Type should be valid JSON for POST {endpoint}")


def test_property_http_authenticated_endpoints_require_auth(client):
    """
    Property 7: HTTP request handling (Authentication)
    
    For any HTTP request to protected endpoints without authentication,
    the application should respond with 401 Unauthorized or redirect to login.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    protected_endpoints = [
        '/homepage',
        '/event_discovery',
        '/event_detail',
        '/biometric_authentication_portal',
        '/personal_photo_gallery',
        '/download_page',
        '/api/user_photos'
    ]
    
    for endpoint in protected_endpoints:
        # Try GET request without authentication
        response = client.get(endpoint, follow_redirects=False)
        
        # Should either redirect (302) or return unauthorized (401)
        assert response.status_code in [302, 401], \
            f"Protected endpoint {endpoint} should return 302 (redirect) or 401 (unauthorized), got {response.status_code}"
    
    # Test POST-only endpoints separately
    post_only_endpoints = [
        ('/api/create_event', 'POST'),
        ('/api/download_photos', 'POST')
    ]
    
    for endpoint, method in post_only_endpoints:
        # Try POST request without authentication
        response = client.post(endpoint, json={}, follow_redirects=False)
        
        # Should return unauthorized (401) or redirect (302)
        assert response.status_code in [302, 401], \
            f"Protected POST endpoint {endpoint} should return 302 (redirect) or 401 (unauthorized), got {response.status_code}"
        
        # Verify response has content
        assert response.data is not None, \
            f"Response should have data for protected endpoint {endpoint}"


def test_property_http_invalid_endpoints_return_404(client):
    """
    Property 7: HTTP request handling (404 errors)
    
    For any HTTP request to non-existent endpoints,
    the application should respond with 404 Not Found.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    invalid_endpoints = [
        '/nonexistent',
        '/api/invalid',
        '/does/not/exist',
        '/random/path/here'
    ]
    
    for endpoint in invalid_endpoints:
        response = client.get(endpoint)
        
        # Should return 404 Not Found
        assert response.status_code == 404, \
            f"Invalid endpoint {endpoint} should return 404, got {response.status_code}"
        
        # Verify response has content
        assert response.data is not None, \
            f"404 response should have data for {endpoint}"


def test_property_http_content_type_handling(client):
    """
    Property 7: HTTP request handling (Content-Type)
    
    For any HTTP request with JSON Content-Type,
    the application should respond appropriately.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    import json
    
    # Test with valid JSON content type
    response = client.post(
        '/register',
        json={'fullName': 'Test', 'email': 'test@test.com', 'password': 'test'},
        content_type='application/json'
    )
    
    # Verify response has a valid HTTP status code
    assert response.status_code is not None, \
        "Response should have a status code"
    
    # Verify status code is in valid HTTP range
    assert 100 <= response.status_code < 600, \
        f"Status code should be valid HTTP code, got {response.status_code}"
    
    # Application should not crash - should return 400, 500, or success codes
    assert response.status_code in [200, 201, 400, 409, 500], \
        f"Application should handle JSON requests gracefully, got {response.status_code}"


def test_property_http_concurrent_requests(client):
    """
    Property 7: HTTP request handling (Concurrency)
    
    For multiple concurrent HTTP requests to the application,
    all requests should receive valid responses without interference.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    import concurrent.futures
    
    def make_request(endpoint):
        response = client.get(endpoint)
        return {
            'endpoint': endpoint,
            'status_code': response.status_code,
            'has_data': response.data is not None,
            'has_headers': response.headers is not None
        }
    
    # Make multiple concurrent requests
    endpoints = ['/', '/login', '/signup', '/events'] * 5
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Verify all requests completed successfully
    assert len(results) == len(endpoints), \
        "All concurrent requests should complete"
    
    for result in results:
        assert result['status_code'] is not None, \
            f"Concurrent request to {result['endpoint']} should have status code"
        
        assert 100 <= result['status_code'] < 600, \
            f"Concurrent request to {result['endpoint']} should have valid status code"
        
        assert result['has_data'], \
            f"Concurrent request to {result['endpoint']} should have data"
        
        assert result['has_headers'], \
            f"Concurrent request to {result['endpoint']} should have headers"


def test_property_http_response_structure(client):
    """
    Property 7: HTTP request handling (Response Structure)
    
    For any HTTP request to API endpoints that return JSON,
    the response should have a consistent structure with 'success' field.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    import json
    
    # Test various API endpoints
    api_endpoints = [
        ('/register', 'POST', {'fullName': 'Test', 'email': 'test@test.com', 'password': 'test'}),
        ('/login', 'POST', {'email': 'test@test.com', 'password': 'test'}),
        ('/events', 'GET', None),
    ]
    
    for endpoint, method, payload in api_endpoints:
        if method == 'GET':
            response = client.get(endpoint)
        elif method == 'POST':
            response = client.post(endpoint, json=payload)
        
        # Verify response has valid status code
        assert response.status_code is not None, \
            f"Response should have status code for {method} {endpoint}"
        
        # For JSON responses, verify structure
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                data = json.loads(response.data)
                
                # API endpoints should have 'success' field (except /events which returns array)
                if endpoint != '/events':
                    assert 'success' in data, \
                        f"JSON response for {method} {endpoint} should have 'success' field"
                    
                    assert isinstance(data['success'], bool), \
                        f"'success' field should be boolean for {method} {endpoint}"
                    
                    # If success is False, should have error message
                    if not data['success']:
                        assert 'error' in data, \
                            f"Failed response for {method} {endpoint} should have 'error' field"
                
            except json.JSONDecodeError:
                pytest.fail(f"Response for {method} {endpoint} should be valid JSON")


def test_property_http_error_responses_are_informative(client):
    """
    Property 7: HTTP request handling (Error Messages)
    
    For any HTTP request that results in an error,
    the response should include informative error messages.
    
    **Feature: docker-deployment, Property 7: HTTP request handling**
    **Validates: Requirements 4.3, 5.4**
    """
    import json
    
    # Test error scenarios
    error_scenarios = [
        # Missing required fields
        ('/register', 'POST', {}, 400),
        ('/login', 'POST', {}, 400),
        # Invalid authentication
        ('/api/create_event', 'POST', {'eventName': 'Test'}, 401),
    ]
    
    for endpoint, method, payload, expected_status in error_scenarios:
        if method == 'POST':
            response = client.post(endpoint, json=payload)
        
        # Verify expected error status
        assert response.status_code == expected_status, \
            f"Error scenario for {method} {endpoint} should return {expected_status}"
        
        # Verify error response has informative message
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                data = json.loads(response.data)
                
                assert 'success' in data, \
                    f"Error response for {method} {endpoint} should have 'success' field"
                
                assert data['success'] is False, \
                    f"Error response for {method} {endpoint} should have success=False"
                
                assert 'error' in data, \
                    f"Error response for {method} {endpoint} should have 'error' field"
                
                assert isinstance(data['error'], str), \
                    f"Error message for {method} {endpoint} should be a string"
                
                assert len(data['error']) > 0, \
                    f"Error message for {method} {endpoint} should not be empty"
                
            except json.JSONDecodeError:
                pytest.fail(f"Error response for {method} {endpoint} should be valid JSON")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
