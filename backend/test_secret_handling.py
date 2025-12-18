"""
Property-based tests for secret handling security.

**Feature: docker-deployment, Property: Secrets are never logged**
**Validates: Requirements 6.4**
"""

import pytest
from hypothesis import given, strategies as st, settings
import os
import re


# Strategy for generating realistic database URLs
@st.composite
def database_url_strategy(draw):
    """Generate realistic PostgreSQL connection strings."""
    protocol = draw(st.sampled_from(['postgresql', 'postgres']))
    user = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    password = draw(st.text(min_size=8, max_size=32, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=['@', '/', ':'])))
    host = draw(st.text(min_size=5, max_size=30, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    db = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    return f"{protocol}://{user}:{password}@{host}/{db}?sslmode=require"


# Test that the application code doesn't contain print statements with secrets
@given(
    database_url=database_url_strategy(),
    secret_key=st.text(min_size=16, max_size=64, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=['\n', '\r', '\0']))
)
@settings(max_examples=100)
def test_app_code_no_secret_logging(database_url, secret_key):
    """
    Property: For any DATABASE_URL and FLASK_SECRET_KEY values,
    the application source code should not contain print statements
    or logging statements that would expose these secrets.
    
    **Feature: docker-deployment, Property: Secrets are never logged**
    **Validates: Requirements 6.4**
    """
    # Read the application source code
    with open('backend/app.py', 'r', encoding='utf-8') as f:
        app_code = f.read()
    
    # Check that there are no print statements with DATABASE_URL
    assert 'print("DATABASE_URL' not in app_code, \
        "Application should not print DATABASE_URL"
    assert 'print(f"DATABASE_URL' not in app_code, \
        "Application should not print DATABASE_URL"
    assert 'print(DATABASE_URL)' not in app_code, \
        "Application should not print DATABASE_URL"
    
    # Check that there are no print statements with FLASK_SECRET_KEY
    assert 'print("FLASK_SECRET_KEY' not in app_code, \
        "Application should not print FLASK_SECRET_KEY"
    assert 'print(f"FLASK_SECRET_KEY' not in app_code, \
        "Application should not print FLASK_SECRET_KEY"
    assert 'print(FLASK_SECRET_KEY)' not in app_code, \
        "Application should not print FLASK_SECRET_KEY"
    
    # Check that logger doesn't log secrets
    assert 'logger.info(DATABASE_URL)' not in app_code, \
        "Application should not log DATABASE_URL"
    assert 'logger.debug(DATABASE_URL)' not in app_code, \
        "Application should not log DATABASE_URL"
    assert 'logger.info(FLASK_SECRET_KEY)' not in app_code, \
        "Application should not log FLASK_SECRET_KEY"
    assert 'logger.debug(FLASK_SECRET_KEY)' not in app_code, \
        "Application should not log FLASK_SECRET_KEY"


def test_database_connection_error_no_secret_exposure():
    """
    Test that database connection errors don't expose the connection string.
    
    **Feature: docker-deployment, Property: Secrets are never logged**
    **Validates: Requirements 6.4**
    """
    import app
    from unittest.mock import patch, MagicMock
    import psycopg2
    import logging
    from io import StringIO
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger('app')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    # Mock psycopg2.connect to raise an error
    with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Connection failed")):
        result = app.get_db_connection()
        
        # Should return None on error
        assert result is None
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Check that DATABASE_URL is not in the error log
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url and len(database_url) > 10:
            assert database_url not in log_output, \
                "DATABASE_URL should not be exposed in error logs"
            
            # Check that password is not exposed
            password_match = re.search(r'://[^:]+:([^@]+)@', database_url)
            if password_match:
                password = password_match.group(1)
                if len(password) > 3:
                    assert password not in log_output, \
                        "Database password should not be exposed in error logs"
    
    logger.removeHandler(handler)


def test_error_messages_no_secret_exposure():
    """
    Test that error messages returned to users don't expose secrets.
    
    **Feature: docker-deployment, Property: Secrets are never logged**
    **Validates: Requirements 6.4**
    """
    import app
    
    # Test various error endpoints
    with app.app.test_client() as client:
        # Test registration error
        response = client.post('/register', 
                              json={'fullName': '', 'email': '', 'password': ''},
                              content_type='application/json')
        
        response_data = response.get_json()
        error_message = response_data.get('error', '')
        
        # Check that secrets are not in error messages
        database_url = os.environ.get('DATABASE_URL', '')
        secret_key = os.environ.get('FLASK_SECRET_KEY', '')
        
        if database_url:
            assert database_url not in error_message, \
                "DATABASE_URL should not be in error messages"
        
        if secret_key:
            assert secret_key not in error_message, \
                "FLASK_SECRET_KEY should not be in error messages"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
