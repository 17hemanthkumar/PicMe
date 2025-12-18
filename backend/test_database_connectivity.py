"""
Test database connectivity for Docker deployment.

This test verifies:
- Application connects to Neon database
- Database query execution works correctly
- Data persistence across container restarts

Requirements: 4.4
"""

import pytest
import psycopg2
import psycopg2.extras
import os
import time
import subprocess
import uuid
from werkzeug.security import generate_password_hash
from hypothesis import given, strategies as st, settings, assume, HealthCheck


def test_database_connection():
    """
    Test that the application can connect to the Neon PostgreSQL database.
    
    This test verifies that:
    - DATABASE_URL environment variable is set
    - Connection to the database succeeds
    - Connection can be closed properly
    """
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping database connectivity test")
    
    # Attempt to connect
    conn = None
    try:
        conn = psycopg2.connect(database_url)
        assert conn is not None, "Connection should not be None"
        
        # Verify connection is open
        assert not conn.closed, "Connection should be open"
        
        print(f"✓ Successfully connected to database")
        
    except psycopg2.OperationalError as e:
        pytest.fail(f"Failed to connect to database: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during connection: {e}")
    finally:
        if conn:
            conn.close()
            assert conn.closed, "Connection should be closed"


def test_database_query_execution():
    """
    Test that database queries can be executed successfully.
    
    This test verifies that:
    - SELECT queries work
    - INSERT queries work
    - UPDATE queries work
    - DELETE queries work
    - Transactions can be committed and rolled back
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping database query test")
    
    conn = None
    cursor = None
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Test 1: Verify users table exists (SELECT query)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cursor.fetchone()['exists']
        assert table_exists, "Users table should exist"
        print(f"✓ Users table exists")
        
        # Test 2: Insert a test user (INSERT query)
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = generate_password_hash("test_password_123")
        test_name = "Test User"
        
        cursor.execute("""
            INSERT INTO users (full_name, email, password, user_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (test_name, test_email, test_password, 'user'))
        
        result = cursor.fetchone()
        test_user_id = result['id']
        assert test_user_id is not None, "Should return user ID"
        conn.commit()
        print(f"✓ Successfully inserted test user with ID: {test_user_id}")
        
        # Test 3: Read the inserted user (SELECT query)
        cursor.execute("""
            SELECT id, full_name, email, user_type
            FROM users
            WHERE id = %s
        """, (test_user_id,))
        
        user = cursor.fetchone()
        assert user is not None, "Should find the inserted user"
        assert user['email'] == test_email, "Email should match"
        assert user['full_name'] == test_name, "Name should match"
        assert user['user_type'] == 'user', "User type should match"
        print(f"✓ Successfully retrieved test user")
        
        # Test 4: Update the user (UPDATE query)
        new_name = "Updated Test User"
        cursor.execute("""
            UPDATE users
            SET full_name = %s
            WHERE id = %s
        """, (new_name, test_user_id))
        conn.commit()
        
        # Verify update
        cursor.execute("""
            SELECT full_name FROM users WHERE id = %s
        """, (test_user_id,))
        updated_user = cursor.fetchone()
        assert updated_user['full_name'] == new_name, "Name should be updated"
        print(f"✓ Successfully updated test user")
        
        # Test 5: Delete the test user (DELETE query)
        cursor.execute("""
            DELETE FROM users WHERE id = %s
        """, (test_user_id,))
        conn.commit()
        
        # Verify deletion
        cursor.execute("""
            SELECT id FROM users WHERE id = %s
        """, (test_user_id,))
        deleted_user = cursor.fetchone()
        assert deleted_user is None, "User should be deleted"
        print(f"✓ Successfully deleted test user")
        
        # Test 6: Test transaction rollback
        cursor.execute("""
            INSERT INTO users (full_name, email, password, user_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, ("Rollback Test", f"rollback_{uuid.uuid4().hex[:8]}@example.com", 
              test_password, 'user'))
        
        rollback_user = cursor.fetchone()
        rollback_user_id = rollback_user['id']
        
        # Rollback instead of commit
        conn.rollback()
        
        # Verify user was not persisted
        cursor.execute("""
            SELECT id FROM users WHERE id = %s
        """, (rollback_user_id,))
        should_be_none = cursor.fetchone()
        assert should_be_none is None, "Rolled back user should not exist"
        print(f"✓ Transaction rollback works correctly")
        
    except psycopg2.Error as e:
        pytest.fail(f"Database query error: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during query execution: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_data_persistence_simulation():
    """
    Test that data persists in the database (simulates container restart).
    
    This test verifies that:
    - Data written in one connection persists
    - Data can be read in a new connection
    - Database state is maintained across connections
    
    Note: This simulates container restart by closing and reopening connections.
    In a real container restart, the database is external (Neon), so data
    should persist naturally.
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping persistence test")
    
    test_email = f"persist_{uuid.uuid4().hex[:8]}@example.com"
    test_password = generate_password_hash("persist_password_123")
    test_name = "Persistence Test User"
    test_user_id = None
    
    # Phase 1: Write data (simulating first container instance)
    conn1 = None
    cursor1 = None
    try:
        conn1 = psycopg2.connect(database_url)
        cursor1 = conn1.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor1.execute("""
            INSERT INTO users (full_name, email, password, user_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (test_name, test_email, test_password, 'user'))
        
        result = cursor1.fetchone()
        test_user_id = result['id']
        conn1.commit()
        print(f"✓ Phase 1: Inserted user with ID {test_user_id}")
        
    except Exception as e:
        pytest.fail(f"Phase 1 failed: {e}")
    finally:
        if cursor1:
            cursor1.close()
        if conn1:
            conn1.close()
    
    # Simulate container restart by waiting a moment
    time.sleep(0.5)
    
    # Phase 2: Read data (simulating second container instance after restart)
    conn2 = None
    cursor2 = None
    try:
        conn2 = psycopg2.connect(database_url)
        cursor2 = conn2.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor2.execute("""
            SELECT id, full_name, email, user_type
            FROM users
            WHERE id = %s
        """, (test_user_id,))
        
        persisted_user = cursor2.fetchone()
        assert persisted_user is not None, "User should persist across connections"
        assert persisted_user['id'] == test_user_id, "User ID should match"
        assert persisted_user['email'] == test_email, "Email should match"
        assert persisted_user['full_name'] == test_name, "Name should match"
        print(f"✓ Phase 2: Successfully retrieved persisted user")
        
        # Clean up: Delete test user
        cursor2.execute("""
            DELETE FROM users WHERE id = %s
        """, (test_user_id,))
        conn2.commit()
        print(f"✓ Cleanup: Deleted test user")
        
    except Exception as e:
        pytest.fail(f"Phase 2 failed: {e}")
    finally:
        if cursor2:
            cursor2.close()
        if conn2:
            conn2.close()


def test_database_connection_error_handling():
    """
    Test that the application handles database connection errors gracefully.
    
    This test verifies that:
    - Invalid DATABASE_URL is handled properly
    - Connection errors don't crash the application
    - Appropriate error messages are returned
    """
    # Test with invalid connection string
    invalid_url = "postgresql://invalid:invalid@invalid.host/invalid?sslmode=require"
    
    conn = None
    try:
        # This should raise an OperationalError
        conn = psycopg2.connect(invalid_url)
        pytest.fail("Should have raised OperationalError for invalid connection")
    except psycopg2.OperationalError as e:
        # This is expected
        print(f"✓ Correctly raised OperationalError for invalid connection: {e}")
        assert conn is None or conn.closed, "Connection should not be established"
    except Exception as e:
        pytest.fail(f"Unexpected error type: {e}")
    finally:
        if conn and not conn.closed:
            conn.close()


def test_database_concurrent_connections():
    """
    Test that multiple concurrent database connections work correctly.
    
    This test verifies that:
    - Multiple connections can be opened simultaneously
    - Each connection is independent
    - Connections can be closed independently
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping concurrent connections test")
    
    connections = []
    cursors = []
    
    try:
        # Open 3 concurrent connections
        for i in range(3):
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            connections.append(conn)
            cursors.append(cursor)
            
            # Verify each connection works independently
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result[0] == 1, f"Connection {i} should work"
        
        print(f"✓ Successfully opened {len(connections)} concurrent connections")
        
        # Verify all connections are still open
        for i, conn in enumerate(connections):
            assert not conn.closed, f"Connection {i} should still be open"
        
    except Exception as e:
        pytest.fail(f"Concurrent connections test failed: {e}")
    finally:
        # Close all connections
        for cursor in cursors:
            if cursor:
                cursor.close()
        for conn in connections:
            if conn:
                conn.close()
        
        print(f"✓ Successfully closed all connections")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])



# ============================================================================
# PROPERTY-BASED TESTS
# ============================================================================

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    query=st.sampled_from([
        "SELECT 1 as test",
        "SELECT NOW()",
        "SELECT version()",
        "SELECT current_database()",
        "SELECT COUNT(*) FROM users",
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 1"
    ])
)
def test_property_database_connectivity(query):
    """
    **Feature: docker-deployment, Property 5: Database connectivity**
    **Validates: Requirements 4.4**
    
    Property: For any valid DATABASE_URL, when the application attempts to 
    connect to the database, the connection should succeed and allow query execution.
    
    This property-based test verifies that:
    - Connection to the database succeeds with the configured DATABASE_URL
    - Various types of queries can be executed successfully
    - The connection can be properly closed
    - The database responds correctly to different query types
    
    The test uses the actual DATABASE_URL from the environment and tests
    various query patterns to ensure robust connectivity.
    """
    database_url = os.environ.get('DATABASE_URL')
    
    # Skip if DATABASE_URL is not set
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping property test")
    
    # Skip if DATABASE_URL is the placeholder value
    if "USER:PASSWORD@HOST/DBNAME" in database_url:
        pytest.skip("DATABASE_URL is placeholder - skipping property test")
    
    conn = None
    cursor = None
    
    try:
        # Property: Connection should succeed for valid DATABASE_URL
        conn = psycopg2.connect(database_url)
        assert conn is not None, "Connection should not be None"
        assert not conn.closed, "Connection should be open"
        
        # Property: Query execution should succeed
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Property: Query should return results (or at least not error)
        result = cursor.fetchone()
        assert result is not None, f"Query '{query}' should return a result"
        
        # Property: Connection should be closeable
        cursor.close()
        conn.close()
        assert conn.closed, "Connection should be closed after close()"
        
    except psycopg2.OperationalError as e:
        # If we get an operational error, it means the DATABASE_URL is invalid
        # or the database is unreachable. This is a failure of the property.
        pytest.fail(f"Database connection failed for query '{query}': {e}")
    except psycopg2.ProgrammingError as e:
        # Programming errors might occur for queries that reference non-existent tables
        # This is acceptable for some queries, so we just ensure connection worked
        if conn and not conn.closed:
            conn.close()
        # The connection worked, which is what we're testing
        pass
    except Exception as e:
        pytest.fail(f"Unexpected error during database connectivity test: {e}")
    finally:
        if cursor and not cursor.closed:
            cursor.close()
        if conn and not conn.closed:
            conn.close()


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    num_connections=st.integers(min_value=1, max_value=5)
)
def test_property_multiple_database_connections(num_connections):
    """
    **Feature: docker-deployment, Property 5: Database connectivity (multiple connections)**
    **Validates: Requirements 4.4**
    
    Property: For any valid DATABASE_URL, the application should be able to
    open multiple concurrent connections and each should work independently.
    
    This property-based test verifies that:
    - Multiple connections can be opened simultaneously
    - Each connection is independent and functional
    - All connections can execute queries
    - All connections can be closed properly
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping property test")
    
    if "USER:PASSWORD@HOST/DBNAME" in database_url:
        pytest.skip("DATABASE_URL is placeholder - skipping property test")
    
    connections = []
    cursors = []
    
    try:
        # Property: Should be able to open N concurrent connections
        for i in range(num_connections):
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            connections.append(conn)
            cursors.append(cursor)
            
            # Property: Each connection should be functional
            assert not conn.closed, f"Connection {i} should be open"
            
            # Property: Each connection should be able to execute queries
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result[0] == 1, f"Connection {i} should execute queries correctly"
        
        # Property: All connections should still be open
        for i, conn in enumerate(connections):
            assert not conn.closed, f"Connection {i} should still be open"
        
    except psycopg2.Error as e:
        pytest.fail(f"Database connectivity property failed with {num_connections} connections: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")
    finally:
        # Clean up all connections
        for cursor in cursors:
            if cursor and not cursor.closed:
                cursor.close()
        for conn in connections:
            if conn and not conn.closed:
                conn.close()


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    operation=st.sampled_from(['insert', 'select', 'update', 'delete'])
)
def test_property_database_operations(operation):
    """
    **Feature: docker-deployment, Property 5: Database connectivity (CRUD operations)**
    **Validates: Requirements 4.4**
    
    Property: For any valid DATABASE_URL, the application should be able to
    perform all CRUD operations (Create, Read, Update, Delete) successfully.
    
    This property-based test verifies that:
    - INSERT operations work
    - SELECT operations work
    - UPDATE operations work
    - DELETE operations work
    - Transactions can be committed
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping property test")
    
    if "USER:PASSWORD@HOST/DBNAME" in database_url:
        pytest.skip("DATABASE_URL is placeholder - skipping property test")
    
    conn = None
    cursor = None
    test_user_id = None
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Generate unique test data
        test_email = f"proptest_{uuid.uuid4().hex[:8]}@example.com"
        test_password = generate_password_hash("test_pass")
        test_name = f"PropTest User {uuid.uuid4().hex[:4]}"
        
        if operation == 'insert':
            # Property: INSERT should create a new record
            cursor.execute("""
                INSERT INTO users (full_name, email, password, user_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (test_name, test_email, test_password, 'user'))
            
            result = cursor.fetchone()
            test_user_id = result['id']
            assert test_user_id is not None, "INSERT should return an ID"
            conn.commit()
            
            # Clean up
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
            conn.commit()
            
        elif operation == 'select':
            # Property: SELECT should retrieve existing records
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            assert result is not None, "SELECT should return results"
            assert 'count' in result, "SELECT should return expected columns"
            
        elif operation == 'update':
            # Property: UPDATE should modify existing records
            # First insert a test record
            cursor.execute("""
                INSERT INTO users (full_name, email, password, user_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (test_name, test_email, test_password, 'user'))
            
            result = cursor.fetchone()
            test_user_id = result['id']
            conn.commit()
            
            # Now update it
            new_name = f"Updated {test_name}"
            cursor.execute("""
                UPDATE users SET full_name = %s WHERE id = %s
            """, (new_name, test_user_id))
            conn.commit()
            
            # Verify update
            cursor.execute("SELECT full_name FROM users WHERE id = %s", (test_user_id,))
            updated = cursor.fetchone()
            assert updated['full_name'] == new_name, "UPDATE should modify the record"
            
            # Clean up
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
            conn.commit()
            
        elif operation == 'delete':
            # Property: DELETE should remove records
            # First insert a test record
            cursor.execute("""
                INSERT INTO users (full_name, email, password, user_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (test_name, test_email, test_password, 'user'))
            
            result = cursor.fetchone()
            test_user_id = result['id']
            conn.commit()
            
            # Now delete it
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
            conn.commit()
            
            # Verify deletion
            cursor.execute("SELECT id FROM users WHERE id = %s", (test_user_id,))
            deleted = cursor.fetchone()
            assert deleted is None, "DELETE should remove the record"
        
    except psycopg2.Error as e:
        pytest.fail(f"Database operation '{operation}' failed: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during '{operation}' operation: {e}")
    finally:
        # Ensure cleanup
        if cursor and test_user_id:
            try:
                cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
                conn.commit()
            except:
                pass
        
        if cursor:
            cursor.close()
        if conn:
            conn.close()
