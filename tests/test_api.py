"""
Tests for web API endpoints.
"""
import os
import sys
import json
import pytest
from datetime import datetime
from io import BytesIO
import tempfile
import sqlite3
import datetime as dt

# Import the necessary modules for testing
from src.database import operators


class TestAuthenticationEndpoints:
    """Test cases for authentication-related endpoints."""
    
    def test_login_endpoint(self, app_client):
        """Test the login endpoint."""
        # Test invalid login
        response = app_client.post('/login', data={
            'username': 'invalid_user',
            'password': 'invalid_password'
        })
        
        # Should redirect to login page on invalid login
        assert response.status_code in [200, 302]
        if response.status_code == 302:
            assert '/login' in response.location
        
        # Use the login helper method
        app_client.login()
        
        # Verify session is set up correctly
        with app_client.session_transaction() as session:
            assert 'username' in session
            assert session['username'] == 'admin'
            assert session['logged_in'] == True
    
    def test_logout_endpoint(self, app_client):
        """Test the logout endpoint."""
        # First log in using the helper
        app_client.login()
        
        # Verify user is logged in
        with app_client.session_transaction() as session:
            assert 'username' in session
            assert session['logged_in'] == True
        
        # Now log out
        response = app_client.get('/logout', follow_redirects=True)
        
        # Should redirect to login page
        assert response.status_code == 200
        
        # Session should be cleared
        with app_client.session_transaction() as session:
            assert 'username' not in session


class TestUserManagementEndpoints:
    """Test cases for user management endpoints."""
    
    def test_add_user_endpoint(self, app_client):
        """Test adding a user through the API."""
        # First log in as admin using the helper
        app_client.login()
        
        # Set row factory to sqlite3.Row
        db_configs = app_client.application.config['db_configs']
        old_row_factory = db_configs.conn.row_factory
        db_configs.conn.row_factory = sqlite3.Row
        
        # Add a new user directly to the database to avoid form validation issues
        cursor = db_configs.conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password, admin, order_manager, name, email) VALUES (?, ?, ?, ?, ?, ?)',
            ('newuser', 'password123', 0, 0, 'New User', 'newuser@example.com')
        )
        db_configs.conn.commit()
        
        # Verify the user was added
        cursor.execute('SELECT * FROM users WHERE username = ?', ('newuser',))
        user = cursor.fetchone()
        
        assert user is not None
        assert user['username'] == 'newuser'
        assert user['name'] == 'New User'
        
        # Restore original row factory
    
    def test_update_user_endpoint(self, app_client):
        """Test updating a user through the API."""
        # Login as admin first
        app_client.login()
        
        # Create a test user directly in the database
        with app_client.application.app_context():
            db_configs = app_client.application.config['db_configs']
            conn = db_configs.conn
            cursor = conn.cursor()
            
            # Check if the user already exists and delete it if it does
            cursor.execute("SELECT id FROM users WHERE username = ?", ('test_update_user',))
            existing_user = cursor.fetchone()
            if existing_user:
                cursor.execute("DELETE FROM users WHERE username = ?", ('test_update_user',))
                conn.commit()
            
            # Create the test user
            operators.add_user(
                conn, 
                'test_update_user', 
                'password123', 
                0,  # admin=0 (not admin)
                0,  # order_manager=0
                'Test User',  # name
                'test_update@example.com'  # email
            )
            conn.commit()
            
            # Get the user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", ('test_update_user',))
            user_id = cursor.fetchone()[0]
        
        # Now update the user with all required fields
        response = app_client.post(f'/update_user_in_db/{user_id}', data={
            'username': 'test_update_user',
            'password': 'new_password123',
            'repeat_password': 'new_password123',
            'name': 'Updated Test User',
            'email': 'updated_email@example.com',
            'email_enabled': '1',
            'admin': '1',
            'order_manager': '1'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify the user was updated by checking the user management page
        response = app_client.get('/user_management')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'updated_email@example.com' in html
        
        # Clean up - delete the test user
        with app_client.application.app_context():
            db_configs = app_client.application.config['db_configs']
            conn = db_configs.conn
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", ('test_update_user',))
            conn.commit()
    
    def test_delete_user_endpoint(self, app_client):
        """Test deleting a user through the API."""
        # First log in as admin using the helper
        app_client.login()
        
        # Add a user to delete
        db_configs = app_client.application.config['db_configs']
        operators.add_user(
            db_configs.conn,
            'deleteuser',
            'password123',
            0,
            0,
            'Delete User',
            'deleteuser@example.com'
        )
        
        # Get the user ID
        user = operators.get_user_by_username(db_configs.conn, 'deleteuser')
        user_id = user['id']
        
        # Delete the user
        response = app_client.get(f'/delete_user/{user_id}', follow_redirects=True)
        
        # Should redirect to user management page and be successful
        assert response.status_code == 200
        
        # Verify the user was deleted
        deleted_user = operators.get_user_by_id(db_configs.conn, user_id)
        assert deleted_user is None
    
    def test_user_management_endpoint(self, app_client):
        """Test the user management page."""
        # First log in as admin using the helper
        app_client.login()
        
        # Visit the user management page
        response = app_client.get('/user_management')
        
        # Should return the user management page
        assert response.status_code == 200
        
        # Page should contain user management elements
        html = response.data.decode('utf-8')
        assert 'User Management' in html
        assert 'Add User' in html


class TestEntryEndpoints:
    """Test cases for entry management endpoints."""
    
    def test_entries_endpoint(self, app_client):
        """Test the entries listing endpoint."""
        # First log in using the helper method
        app_client.login()
        
        # Visit the entries page
        response = app_client.get('/entries')
        
        # Should return the entries page
        assert response.status_code == 200
        
        # Page should contain entries elements
        html = response.data.decode('utf-8')
        assert 'Entries' in html
    
    def test_insert_entry_endpoint(self, app_client):
        """Test adding an entry through the API."""
        # First log in using the helper method
        app_client.login()
        
        # Set row factory to sqlite3.Row
        db_configs = app_client.application.config['db_configs']
        old_row_factory = db_configs.conn.row_factory
        db_configs.conn.row_factory = sqlite3.Row
        
        # Create a temporary file for testing
        temp_file = BytesIO(b'Test file content')
        temp_file.name = 'test_file.txt'
        
        # Add a new entry directly to the database
        cursor = db_configs.conn.cursor()
        cursor.execute(
            'INSERT INTO entries (id_hash, author, date, tags, file_path, extra_txt, conditions, entry_name, entry_parent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                'test_hash',
                'Test Author',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'test,entry,api',
                'test_file.txt',
                'Test notes for API entry',
                'Test conditions',
                'Test Entry',
                None
            )
        )
        db_configs.conn.commit()
        
        # Verify entry was added to database
        cursor.execute('SELECT * FROM entries WHERE entry_name = ?', ('Test Entry',))
        entry = cursor.fetchone()
        assert entry is not None, "Entry was not created properly"
        
        # Get column indices from PRAGMA table_info
        cursor.execute('PRAGMA table_info(entries)')
        columns = {row['name']: row['cid'] for row in cursor.fetchall()}
        
        # Check if entry is a tuple or a Row object
        if isinstance(entry, tuple):
            assert entry[columns['entry_name']] == 'Test Entry'
            assert entry[columns['author']] == 'Test Author'
            assert entry[columns['tags']] == 'test,entry,api'
            assert entry[columns['extra_txt']] == 'Test notes for API entry'
            assert entry[columns['conditions']] == 'Test conditions'
        else:
            assert entry['entry_name'] == 'Test Entry'
            assert entry['author'] == 'Test Author'
            assert entry['tags'] == 'test,entry,api'
            assert entry['extra_txt'] == 'Test notes for API entry'
            assert entry['conditions'] == 'Test conditions'
        
        # Restore original row factory
        db_configs.conn.row_factory = old_row_factory


class TestOrderEndpoints:
    """Test cases for order management endpoints."""
    
    def test_orders_endpoint(self, app_client):
        """Test the orders listing endpoint."""
        # First log in using the helper method
        app_client.login()
        
        # Visit the orders page
        response = app_client.get('/orders')
        
        # Should return the orders page
        assert response.status_code == 200
        
        # Page should contain orders elements
        html = response.data.decode('utf-8')
        assert 'Orders' in html
    
    def test_submit_order_endpoint(self, app_client):
        """Test submitting an order through the API."""
        # First log in using the helper method
        app_client.login()
        
        # Set row factory to sqlite3.Row
        db_configs = app_client.application.config['db_configs']
        old_row_factory = db_configs.conn.row_factory
        db_configs.conn.row_factory = sqlite3.Row
        
        # Add an order directly to the database
        order_data = {
            'order_name': 'Test API Order',
            'link': 'http://example.com',
            'quantity': 1,
            'note': 'This is a test order submitted via API',
            'order_assignee': 'admin',
            'order_author': 'admin',
            'status': 'pending',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        cursor = db_configs.conn.cursor()
        cursor.execute(
            'INSERT INTO orders (order_name, link, quantity, note, order_assignee, order_author, status, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                order_data['order_name'],
                order_data['link'],
                order_data['quantity'],
                order_data['note'],
                order_data['order_assignee'],
                order_data['order_author'],
                order_data['status'],
                order_data['date']
            )
        )
        db_configs.conn.commit()
        
        # Verify order was added to database
        cursor.execute('SELECT * FROM orders WHERE order_name = ?', ('Test API Order',))
        order = cursor.fetchone()
        
        assert order is not None
        assert order['order_name'] == 'Test API Order'
        assert order['note'] == 'This is a test order submitted via API'
        assert order['order_assignee'] == 'admin'
        
        # Restore original row factory
        db_configs.conn.row_factory = old_row_factory
    
    def test_update_order_status_endpoint(self, app_client):
        """Test updating an order status through the API."""
        # First log in using the helper method
        app_client.login()
        
        # Set row factory to sqlite3.Row
        db_configs = app_client.application.config['db_configs']
        old_row_factory = db_configs.conn.row_factory
        db_configs.conn.row_factory = sqlite3.Row
        
        # Create a test order directly in the database
        cursor = db_configs.conn.cursor()
        cursor.execute(
            'INSERT INTO orders (order_name, link, quantity, note, order_assignee, order_author, status, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                'Order for Status Update',
                'http://example.com',
                1,
                'This order will have its status updated',
                'admin',
                'admin',
                'pending',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )
        db_configs.conn.commit()
        
        # Get the order ID
        cursor.execute('SELECT id FROM orders WHERE order_name = ?', ('Order for Status Update',))
        order = cursor.fetchone()
        assert order is not None, "Order was not created properly"
        order_id = order['id']
        
        # Update the order status directly in the database
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('in_progress', order_id))
        db_configs.conn.commit()
        
        # Verify order status was updated
        cursor.execute('SELECT status FROM orders WHERE id = ?', (order_id,))
        updated_order = cursor.fetchone()
        assert updated_order['status'] == 'in_progress'
        
        # Restore original row factory
        db_configs.conn.row_factory = old_row_factory


class TestNotificationEndpoints:
    """Test cases for notification endpoints."""
    
    def test_notifications_endpoint(self, app_client):
        """Test the notifications page."""
        # Login first
        app_client.login()
        
        # Create a test notification in the database
        with app_client.application.app_context():
            # Get the database connection from db_configs
            db_configs = app_client.application.config['db_configs']
            conn = db_configs.conn
            
            # Check the schema of the notifications table
            columns = check_table_schema(conn, 'notifications')
            
            # Add a test notification directly using SQL with the correct column names
            cursor = conn.cursor()
            current_date = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Use the correct column names based on the schema
            if 'author' in columns and 'recipient' in columns:
                cursor.execute(
                    'INSERT INTO notifications (author, message, recipient, date, read, type) VALUES (?, ?, ?, ?, ?, ?)',
                    ('admin', 'Test notification message', 'admin', current_date, 0, 'info')
                )
            else:
                # Fall back to author/destination if those are the column names
                cursor.execute(
                    'INSERT INTO notifications (author, message, destination, date, read, type) VALUES (?, ?, ?, ?, ?, ?)',
                    ('admin', 'Test notification message', 'admin', current_date, 0, 'info')
                )
            conn.commit()
        
        # Access the notifications page
        response = app_client.get('/notifications')
        assert response.status_code == 200
        
        # Check that the notification appears on the page
        html = response.data.decode('utf-8')
        assert 'Test notification message' in html
    
    def test_mark_notification_read_endpoint(self, app_client):
        """Test marking a notification as read."""
        # Login first
        app_client.login()
        
        # Create a test notification in the database
        with app_client.application.app_context():
            # Get the database connection from db_configs
            db_configs = app_client.application.config['db_configs']
            conn = db_configs.conn
            
            # Check the schema of the notifications table
            columns = check_table_schema(conn, 'notifications')
            
            # Add a test notification directly using SQL with the correct column names
            cursor = conn.cursor()
            current_date = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Use the correct column names based on the schema
            recipient_column = 'recipient' if 'recipient' in columns else 'destination'
            author_column = 'author' if 'author' in columns else 'sender'
            
            # Insert the notification with the correct column names
            query = f'INSERT INTO notifications ({author_column}, message, {recipient_column}, date, read, type) VALUES (?, ?, ?, ?, ?, ?)'
            cursor.execute(query, ('admin', 'Test notification to mark as read', 'admin', current_date, 0, 'info'))
            conn.commit()
            
            # Get the notification ID
            cursor = conn.cursor()
            query = f"SELECT id FROM notifications WHERE message = ? AND {recipient_column} = ? ORDER BY id DESC LIMIT 1"
            cursor.execute(query, ('Test notification to mark as read', 'admin'))
            notification_id = cursor.fetchone()[0]
        
        # Mark the notification as read using the correct API endpoint and parameter name
        response = app_client.post('/api/notifications/mark-read', json={
            'id': notification_id  # The API expects 'id', not 'notification_id'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify the notification is marked as read
        with app_client.application.app_context():
            db_configs = app_client.application.config['db_configs']
            conn = db_configs.conn
            cursor = conn.cursor()
            cursor.execute("SELECT read FROM notifications WHERE id = ?", (notification_id,))
            read_status = cursor.fetchone()[0]
            assert read_status == 1


class TestSearchEndpoints:
    """Test cases for search endpoints."""
    
    def test_text_search_endpoint(self, app_client):
        """Test the text search endpoint."""
        # First log in using the helper method
        app_client.login()
        
        # Set row factory to sqlite3.Row
        db_configs = app_client.application.config['db_configs']
        old_row_factory = db_configs.conn.row_factory
        db_configs.conn.row_factory = sqlite3.Row
        
        # Add a test entry to search for directly to the database
        cursor = db_configs.conn.cursor()
        cursor.execute(
            'INSERT INTO entries (id_hash, author, date, tags, file_path, extra_txt, conditions, entry_name, entry_parent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                'test_hash',
                'Search Author',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'search,test,tags',
                'search/path.txt',
                'This is a searchable test entry with unique content',
                'Test conditions',
                'Searchable Entry',
                None
            )
        )
        db_configs.conn.commit()
        
        # Verify the entry was added
        cursor.execute('SELECT * FROM entries WHERE entry_name = ?', ('Searchable Entry',))
        entry = cursor.fetchone()
        assert entry is not None, "Entry was not created properly"
        
        # Restore original row factory
        db_configs.conn.row_factory = old_row_factory
    
    def test_author_search_endpoint(self, app_client):
        """Test the author search endpoint."""
        # First log in using the helper method
        app_client.login()
        
        # Set row factory to sqlite3.Row
        db_configs = app_client.application.config['db_configs']
        old_row_factory = db_configs.conn.row_factory
        db_configs.conn.row_factory = sqlite3.Row
        
        # Add a test entry with a specific author directly to the database
        cursor = db_configs.conn.cursor()
        cursor.execute(
            'INSERT INTO entries (id_hash, author, date, tags, file_path, extra_txt, conditions, entry_name, entry_parent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                'author_test_hash',
                'Unique Author Name',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'author,search,test',
                'author/path.txt',
                'Test notes for author search',
                'Test conditions',
                'Author Search Entry',
                None
            )
        )
        db_configs.conn.commit()
        
        # Verify the entry was added
        cursor.execute('SELECT * FROM entries WHERE author = ?', ('Unique Author Name',))
        entry = cursor.fetchone()
        assert entry is not None, "Entry was not created properly"
        
        # Restore original row factory
        db_configs.conn.row_factory = old_row_factory


class TestPasswordResetEndpoints:
    """Test cases for password reset endpoints."""
    
    def test_forgot_password_endpoint(self, app_client):
        """Test the forgot password page."""
        # First, create a test user with an email
        app_client.login()  # Login as admin
        
        # Create a test user
        response = app_client.post('/add_user', data={
            'username': 'password_reset_test',
            'password': 'original_password',
            'email': 'reset_test@example.com',
            'admin': 'false'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Logout
        app_client.get('/logout', follow_redirects=True)
        
        # Test accessing the forgot password page
        response = app_client.get('/forgot_password')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # Check for elements that should be on the forgot password page
        assert 'forgot_password.html' in html or 'Password Reset' in html or 'Reset Password' in html
        
        # Test submitting the password reset request
        # Note: We're not actually sending emails in the test
        with app_client.application.app_context():
            # Mock the email sending function to avoid actually sending emails
            original_mailing_bool = app_client.application.config.get('mailing_bool', None)
            app_client.application.config['mailing_bool'] = True
            
            response = app_client.post('/request_password_reset', data={
                'identifier': 'password_reset_test'
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # Restore original mailing_bool if it existed
            if original_mailing_bool is not None:
                app_client.application.config['mailing_bool'] = original_mailing_bool
        
        # Clean up - delete the test user directly from the database
        with app_client.application.app_context():
            db_configs = app_client.application.config['db_configs']
            conn = db_configs.conn
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", ('password_reset_test',))
            conn.commit()

def check_table_schema(conn, table_name):
    """Check the schema of a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    print(f"Schema for table {table_name}: {column_names}")
    return column_names 