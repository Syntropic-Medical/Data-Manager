"""
Working integration tests for the Data Manager application.
"""
import pytest
from datetime import datetime

class TestBasicIntegration:
    """Basic integration tests that should pass."""
    
    def test_login_functionality(self, app_client):
        """Test that the login functionality works."""
        # Log in as admin using the helper method
        response = app_client.login()
        
        # Check that we can access the entries page (which should be accessible after login)
        entries_response = app_client.get('/entries')
        assert entries_response.status_code == 200
        
        # Log out
        logout_response = app_client.get('/logout')
        assert logout_response.status_code == 302  # Should redirect after logout
        
        # Verify we're redirected when accessing protected page after logout
        after_logout_response = app_client.get('/entries')
        assert after_logout_response.status_code == 302  # Should redirect to login
    
    def test_basic_database_operations(self, db_config):
        """Test basic database operations."""
        from src.database import operators
        
        # Test adding and retrieving a user
        operators.add_user(
            db_config.conn,
            'test_user',
            'test_password',
            0,  # not admin
            0,  # not order manager
            'Test User',
            'test@example.com'
        )
        
        # Retrieve the user
        user = operators.get_user_by_username(db_config.conn, 'test_user')
        assert user is not None
        assert user['username'] == 'test_user'
        assert user['name'] == 'Test User'
        assert user['email'] == 'test@example.com'
    
    def test_basic_search_functionality(self, app_client):
        """Test basic search functionality using the app client."""
        # Log in first
        app_client.login()
        
        # Get the database connection from the app
        db_configs = app_client.application.config['db_configs']
        conn = db_configs.conn
        
        # Add test entry directly to the database
        from src.database import operators
        operators.insert_entry_to_db(
            conn,
            'Test Author',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test,search,integration',
            'path/to/test.txt',
            'Test notes for search',
            'Test conditions',
            'Test Entry Name',
            None
        )
        
        # Test the search endpoints
        text_search_response = app_client.post('/text_search', data={
            'text': 'Test notes'
        })
        assert text_search_response.status_code == 200
        
        author_search_response = app_client.post('/author_search', data={
            'text': 'Test Author'
        })
        assert author_search_response.status_code == 200
        
        tags_search_response = app_client.post('/tags_search', data={
            'text': 'test'
        })
        assert tags_search_response.status_code == 200 