"""
Unit tests for database operators module.
"""
import os
import sys
import pytest
import datetime as dt
from sqlite3 import Error

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the operators module
from src.database import operators

class TestUserOperations:
    """Test cases for user management operations."""

    def test_add_user(self, db_config):
        """Test adding a user to the database."""
        # Add a test user
        result = operators.add_user(
            db_config.conn,
            'testuser',
            'password123',
            0,
            0,
            'Test User',
            'test@example.com'
        )
        
        # Verify user was added successfully
        assert result is True
        
        # Verify user exists in database
        cursor = db_config.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', ('testuser',))
        user = cursor.fetchone()
        
        assert user is not None
        assert user['username'] == 'testuser'
        assert user['name'] == 'Test User'
        assert user['email'] == 'test@example.com'
        assert user['admin'] == 0
        assert user['order_manager'] == 0
        
        # Verify password is hashed
        assert user['password'] != 'password123'
        assert operators.verify_password(user['password'], 'password123')

    def test_get_user_by_username(self, db_config):
        """Test retrieving a user by username."""
        # Add a test user
        operators.add_user(
            db_config.conn,
            'testuser2',
            'password123',
            0,
            0,
            'Test User 2',
            'test2@example.com'
        )
        
        # Retrieve the user
        user = operators.get_user_by_username(db_config.conn, 'testuser2')
        
        # Verify user data
        assert user is not None
        assert user['username'] == 'testuser2'
        assert user['name'] == 'Test User 2'
        assert user['email'] == 'test2@example.com'

    def test_update_user(self, db_config):
        """Test updating user information."""
        # Add a test user
        operators.add_user(
            db_config.conn,
            'testuser3',
            'password123',
            0,
            0,
            'Test User 3',
            'test3@example.com'
        )
        
        # Get user ID
        user = operators.get_user_by_username(db_config.conn, 'testuser3')
        user_id = user['id']
        
        # Update user information
        form_data = {
            'name': 'Updated Name',
            'email': 'updated@example.com',
            'admin': 1,
            'order_manager': 1
        }
        
        result = operators.update_user(db_config.conn, form_data, user_id)
        assert result is True
        
        # Verify user was updated
        updated_user = operators.get_user_by_id(db_config.conn, user_id)
        assert updated_user['name'] == 'Updated Name'
        assert updated_user['email'] == 'updated@example.com'
        assert updated_user['admin'] == 1
        assert updated_user['order_manager'] == 1

    def test_delete_user(self, db_config):
        """Test deleting a user."""
        # Add a test user
        operators.add_user(
            db_config.conn,
            'testuser4',
            'password123',
            0,
            0,
            'Test User 4',
            'test4@example.com'
        )
        
        # Get user ID
        user = operators.get_user_by_username(db_config.conn, 'testuser4')
        user_id = user['id']
        
        # Delete the user
        operators.delete_user(db_config.conn, user_id)
        
        # Verify user no longer exists
        deleted_user = operators.get_user_by_id(db_config.conn, user_id)
        assert deleted_user is None


class TestEntryOperations:
    """Test cases for database entry operations."""
    
    def test_insert_entry(self, db_config):
        """Test inserting an entry into the database."""
        # Add a test entry
        entry_name = "Test Entry"
        author = "Test Author"
        date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tags = "tag1,tag2,tag3"
        file_path = "test/path/to/file.txt"
        notes = "Test notes for the entry"
        conditions = "Test conditions"
        parent_entry = None
        
        # Insert the entry
        entry_id = operators.insert_entry_to_db(
            db_config.conn,
            author,
            date,
            tags,
            file_path,
            notes,
            conditions,
            entry_name,
            parent_entry
        )
        
        # Verify entry was added
        assert entry_id is not None
        
        # Get the entry and verify its data
        entry = operators.get_entry_by_id(db_config.conn, entry_id)
        assert entry is not None
        assert entry['entry_name'] == entry_name
        assert entry['author'] == author
        assert entry['tags'] == tags
        assert entry['file_path'] == file_path
        assert entry['extra_txt'] == notes
        assert entry['conditions'] == conditions
    
    def test_update_entry(self, db_config):
        """Test updating an entry in the database."""
        # Add a test entry
        entry_id = operators.insert_entry_to_db(
            db_config.conn,
            "Original Author",
            dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "original,tags",
            "original/path.txt",
            "Original notes",
            "Original conditions",
            "Original Entry Name",
            None
        )
    
        # Get the hash_id
        hash_id = operators.get_hash_id_by_entry_id(db_config.conn, entry_id)
    
        # Create update form data with the correct keys
        current_date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        post_form = {
            'entry_name': 'Updated Entry Name',
            'Author': 'Updated Author',
            'Tags': 'updated,tags',
            'Notes': 'Updated notes',
            'condition&Updated conditions': 'Updated conditions',  # Format for conditions
            'date': current_date,
            'File_Path': 'updated/path.txt',
            'parent_entry': None
        }
    
        # Mock app_config and Files for the update function
        app_config = {'UPLOAD_FOLDER': '/tmp'}
        files = {}
    
        # Update the entry
        operators.update_entry_in_db(db_config.conn, entry_id[0], post_form, app_config, hash_id, files)
    
        # Get the updated entry
        updated_entry = operators.get_entry_by_id(db_config.conn, entry_id)
    
        # Verify updates
        assert updated_entry['entry_name'] == 'Updated Entry Name'
        assert updated_entry['tags'] == 'updated,tags'
        assert updated_entry['extra_txt'] == 'Updated notes'
        assert updated_entry['file_path'] == 'updated/path.txt'
        assert updated_entry['conditions'] == 'Updated conditions'
    
    def test_delete_entry(self, db_config):
        """Test deleting an entry from the database."""
        # Add a test entry
        entry_id = operators.insert_entry_to_db(
            db_config.conn,
            "Test Author",
            dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test,tags",
            "test/path.txt",
            "Test notes",
            "Test conditions",
            "Test Entry",
            None
        )
    
        # Verify entry exists
        entry = operators.get_entry_by_id(db_config.conn, entry_id)
        assert entry is not None
        
        # Delete the entry
        operators.delete_entry_from_db(db_config.conn, entry_id[0])
        
        # Verify entry no longer exists
        deleted_entry = operators.get_entry_by_id(db_config.conn, entry_id)
        assert deleted_entry is None


class TestOrderOperations:
    """Test cases for order management operations."""
    
    def test_submit_order(self, db_config):
        """Test submitting a new order."""
        # Create order data
        order_data = {
            'order_name': 'Test Order',
            'link': 'http://example.com',
            'quantity': 5,
            'note': 'This is a test order',
            'order_assignee': 'admin',
            'order_author': 'testuser',
            'status': 'pending',
            'date': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Submit the order
        result, order_id = operators.submit_order(db_config.conn, order_data)
        
        # Verify order was created
        assert result is True
        assert order_id is not None
        
        # Retrieve the order
        order = operators.get_order_by_id(db_config.conn, order_id)
        
        # Verify order data
        assert order is not None
        assert order['order_name'] == 'Test Order'
        assert order['link'] == 'http://example.com'
        assert order['quantity'] == 5
        assert order['note'] == 'This is a test order'
        assert order['order_assignee'] == 'admin'
        assert order['order_author'] == 'testuser'
        assert order['status'] == 'pending'
    
    def test_update_order(self, db_config):
        """Test updating an existing order."""
        # Create a test order
        order_data = {
            'order_name': 'Original Order',
            'link': 'http://example.com',
            'quantity': 3,
            'note': 'Original description',
            'order_assignee': 'admin',
            'order_author': 'testuser',
            'status': 'pending',
            'date': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result, order_id = operators.submit_order(db_config.conn, order_data)
        assert result is True
        
        # Update order data
        updated_data = {
            'order_name': 'Updated Order',
            'link': 'http://updated.com',
            'quantity': 10,
            'note': 'Updated description',
            'order_assignee': 'testuser2',
            'status': 'in_progress'
        }
        
        # Update the order
        result = operators.update_order(db_config.conn, order_id, updated_data)
        assert result is True
        
        # Verify the order was updated
        updated_order = operators.get_order_by_id(db_config.conn, order_id)
        assert updated_order is not None
        assert updated_order['order_name'] == 'Updated Order'
        assert updated_order['link'] == 'http://updated.com'
        assert updated_order['quantity'] == 10
        assert updated_order['note'] == 'Updated description'
        assert updated_order['order_assignee'] == 'testuser2'
        assert updated_order['status'] == 'in_progress'
        assert updated_order['order_author'] == 'testuser'  # Should not change
    
    def test_delete_order(self, db_config):
        """Test deleting an order."""
        # Create a test order
        order_data = {
            'order_name': 'Order to Delete',
            'link': 'http://example.com',
            'quantity': 2,
            'note': 'This order will be deleted',
            'order_assignee': 'admin',
            'order_author': 'testuser',
            'status': 'pending',
            'date': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result, order_id = operators.submit_order(db_config.conn, order_data)
        assert result is True
        
        # Verify order exists
        order = operators.get_order_by_id(db_config.conn, order_id)
        assert order is not None
        
        # Delete the order
        result = operators.delete_order(db_config.conn, order_id)
        assert result is True
        
        # Verify order no longer exists
        deleted_order = operators.get_order_by_id(db_config.conn, order_id)
        assert deleted_order is None


class TestNotificationOperations:
    """Test cases for notification operations."""
    
    def test_add_notification(self, db_config):
        """Test adding a notification."""
        # Add a notification
        author = "admin"
        message = "Test notification message"
        recipient = "testuser"
        notification_type = "info"
        reference_id = 123
        
        operators.add_notification(
            db_config.conn,
            author,
            message,
            recipient,
            notification_type,
            reference_id
        )
        
        # Retrieve notifications for the recipient
        notifications = operators.get_notifications(db_config.conn, recipient)
        
        # Verify notification was added
        assert len(notifications) > 0
        notification = notifications[0]
        assert notification['author'] == author
        assert notification['message'] == message
        assert notification['recipient'] == recipient
        assert notification['type'] == notification_type
        assert notification['reference_id'] == reference_id
        assert notification['read'] == 0  # Should be unread by default
    
    def test_mark_notification_read(self, db_config):
        """Test marking a notification as read."""
        # Add a notification
        operators.add_notification(
            db_config.conn,
            "admin",
            "Another test notification",
            "testuser",
            "info"
        )
        
        # Get the notification
        notifications = operators.get_notifications(db_config.conn, "testuser")
        print(notifications)
        notification_id = notifications[0]['id']
        
        # Verify it's unread
        assert notifications[0]['read'] == 0
        
        # Mark as read
        operators.mark_notification_read(db_config.conn, notification_id)
        
        # Verify it's now read
        updated_notifications = operators.get_notifications(db_config.conn, "testuser")
        updated_notification = next(n for n in updated_notifications if n['id'] == notification_id)
        assert updated_notification['read'] == 1
    
    def test_unread_notification_count(self, db_config):
        """Test counting unread notifications."""
        # Add multiple notifications
        operators.add_notification(
            db_config.conn,
            "admin",
            "Notification 1",
            "testuser2",
            "order"
        )
        
        operators.add_notification(
            db_config.conn,
            "admin",
            "Notification 2",
            "testuser2",
            "order"
        )
        
        operators.add_notification(
            db_config.conn,
            "admin",
            "Notification 3",
            "testuser2",
            "order"
        )
        
        # Get the count of unread notifications
        count = operators.get_unread_notification_count(db_config.conn, "testuser2")
        assert count == 3
        
        # Mark one as read
        notifications = operators.get_notifications(db_config.conn, "testuser2")
        operators.mark_notification_read(db_config.conn, notifications[0]['id'])
        
        # Check count again
        updated_count = operators.get_unread_notification_count(db_config.conn, "testuser2")
        assert updated_count == 2


class TestPasswordResetOperations:
    """Test cases for password reset operations."""
    
    def test_password_reset_token(self, db_config):
        """Test creating and retrieving a password reset token."""
        # Create a test user
        operators.add_user(
            db_config.conn,
            'resetuser',
            'password123',
            0,
            0,
            'Reset Test User',
            'reset@example.com'
        )
        
        # Create a token
        token = "test-reset-token"
        expiry = (dt.datetime.now() + dt.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Add the token
        operators.create_password_reset_token(db_config.conn, 'resetuser', token, expiry)
        
        # Retrieve the token
        token_data = operators.get_password_reset_token(db_config.conn, token)
        
        # Verify token data
        assert token_data is not None
        assert token_data['username'] == 'resetuser'
        assert token_data['token'] == token
        
        # Delete the token
        operators.delete_password_reset_token(db_config.conn, token)
        
        # Verify token is gone
        deleted_token = operators.get_password_reset_token(db_config.conn, token)
        assert deleted_token is None


class TestPasswordHashingFunctions:
    """Test cases for password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        # Hash a password
        password = "secure_password123"
        hashed_password = operators.hash_password(password)
        
        # Verify it's properly hashed
        assert hashed_password != password
        assert len(hashed_password) > 0
        
        # Verify correct password verification
        assert operators.verify_password(hashed_password, password) is True
        
        # Verify incorrect password fails
        assert operators.verify_password(hashed_password, "wrong_password") is False
        
        # Test another password to ensure uniqueness of hashes
        another_password = "another_secure_password"
        another_hash = operators.hash_password(another_password)
        
        # Verify hashes are different
        assert hashed_password != another_hash 