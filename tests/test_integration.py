"""
Integration tests for complete user workflows.
"""
import os
import sys
import pytest
import json
from datetime import datetime, timedelta
from io import BytesIO

from src.database import operators


class TestUserWorkflows:
    """Integration tests for complete user workflows."""
    
    def test_user_management_workflow(self, app_client):
        """Test the complete user management workflow."""
        # Log in as admin using the helper method
        app_client.login()
        db_configs = app_client.application.config['db_configs']
        # Go to user management page
        user_management_response = app_client.get('/user_management')
        assert user_management_response.status_code == 200
        # delete the user if it exists
        operators.delete_user(db_configs.conn, 'workflow_user')
        # Add a new user
        add_user_response = app_client.post('/add_user_to_db', data={
            'username': 'workflow_user',
            'password': 'password123',
            'repeat_password': 'password123',
            'name': 'Workflow Test User',
            'email': 'workflow@example.com',
            'admin': '0',
            'order_manager': '1'
        }, follow_redirects=True)
        
        # Check that user was added
        assert add_user_response.status_code == 200
        html = add_user_response.data.decode('utf-8')
        # check that the user was added to the database
        user = operators.get_user_by_username(db_configs.conn, 'workflow_user')
        assert user is not None
        
        user = operators.get_user_by_username(db_configs.conn, 'workflow_user')
        user_id = user['id']
        
        # Update the user
        update_user_response = app_client.post(f'/update_user_in_db/{user_id}', data={
            'name': 'Updated Workflow User',
            'email': 'updated_workflow@example.com',
            'email_enabled': 1,
            'admin': 1,
            'order_manager': 1
        }, follow_redirects=True)
        
        # Check that user was updated
        assert update_user_response.status_code == 200
        html = update_user_response.data.decode('utf-8')
        assert 'Updated Workflow User' in html
        assert 'updated_workflow@example.com' in html
        
        # Delete the user
        delete_user_response = app_client.get(f'/delete_user/{user_id}', follow_redirects=True)
        
        # Check that user was deleted
        assert delete_user_response.status_code == 200
        html = delete_user_response.data.decode('utf-8')
        assert 'Updated Workflow User' not in html
        assert 'updated_workflow@example.com' not in html
        
        # Log out
        logout_response = app_client.get('/logout')
        assert logout_response.status_code == 302
        assert '/login' in logout_response.location
    
    def test_entry_management_workflow(self, app_client):
        """Test the complete entry management workflow."""
        # Log in as admin using the helper method
        app_client.login()
        db_configs = app_client.application.config['db_configs']
        # Go to entries page
        entries_response = app_client.get('/entries')
        assert entries_response.status_code == 200
        
        # Create a temporary file for testing
        temp_file = BytesIO(b'Test workflow file content')
        
        # Add a new entry
        add_entry_response = app_client.post('/insert_entry_to_db', data={
            'entry_name': 'Workflow Test Entry',
            'Tags': 'workflow,test,integration',
            'Notes': 'Test notes for workflow entry',
            'conditions': 'Test workflow conditions',
            'file': (temp_file, 'workflow_test_file.txt'),
            'File_Path': 'workflow/test/integration/workflow_test_file.txt'
        }, follow_redirects=True, content_type='multipart/form-data')

        # check if the entry was added to the database
        assert add_entry_response.status_code == 200
        cursor = db_configs.conn.cursor()
        cursor.execute('SELECT * FROM entries WHERE entry_name = ?', ('Workflow Test Entry',))
        entry = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        entry = dict(zip(columns, entry))
        entry_id = entry['id']
        assert entry_id is not None
        entry_hash_id = entry['id_hash']
        assert entry_hash_id is not None
        entry_date = entry['date']
        assert entry_date is not None
        entry_tags = entry['tags']
        assert entry_tags == 'workflow,test,integration'
        entry_notes = entry['extra_txt']
        assert entry_notes == 'Test notes for workflow entry'
        entry_conditions = entry['conditions']
        assert entry_conditions == 'Test workflow conditions'
        entry_file_path = entry['file_path']
        assert 'workflow_test_file.txt' in entry_file_path

    
        # Get the entry ID
        db_configs = app_client.application.config['db_configs']
        cursor = db_configs.conn.cursor()
        cursor.execute('SELECT id FROM entries WHERE entry_name = ?', ('Workflow Test Entry',))
        entry = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        entry = dict(zip(columns, entry))
        entry_id = entry['id']
        
        # View the entry details
        view_entry_response = app_client.get(f'/entry/{entry_id}')
        assert view_entry_response.status_code == 200
        html = view_entry_response.data.decode('utf-8')

        assert 'Workflow Test Entry' in html
        # assert 'workflow_user' in html
        assert 'workflow,test,integration' in html
        assert 'Test notes for workflow entry' in html
        
        # Update the entry
        update_entry_response = app_client.post(f'/entry/{entry_id}/update_entry', data={
            'entry_name': 'Updated Workflow Entry',
            'Tags': 'updated,workflow,test',
            'Notes': 'Updated test notes',
            'conditions': 'Updated test conditions'
        }, follow_redirects=True)
        
        # Check that entry was updated
        assert update_entry_response.status_code == 200
        html = update_entry_response.data.decode('utf-8')
        assert 'Updated Workflow Entry' in html
        
        # Delete the entry
        delete_entry_response = app_client.get(f'/entry/{entry_id}/delete_entry', follow_redirects=True)
        
        # Check that entry was deleted
        assert delete_entry_response.status_code == 200
        html = delete_entry_response.data.decode('utf-8')
        assert 'Updated Workflow Entry' not in html
    
    def test_order_management_workflow(self, app_client):
        """Test the complete order management workflow."""
        # Log in as admin using the helper method
        app_client.login()
        
        # Go to orders page
        orders_response = app_client.get('/orders')
        assert orders_response.status_code == 200
        
        # Submit a new order
        today = datetime.now().date().isoformat()
        submit_order_response = app_client.post('/submit_order', data={
            'order_name': 'Workflow Test Order',
            'note': 'This is a test order for workflow testing',
            'order_assignee': 'admin',
            'quantity': 10,
            'link': 'https://www.google.com'
        }, follow_redirects=True)
        # Check that order was submitted successfully
        assert submit_order_response.status_code == 200

        # check if the order was added to the databse
        db_configs = app_client.application.config['db_configs']
        cursor = db_configs.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE order_name = ?', ('Workflow Test Order',))
        order = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        order = dict(zip(columns, order))
        order_id = order['id']
        assert order_id is not None
        order_name = order['order_name']
        assert order_name == 'Workflow Test Order'
        order_note = order['note']
        assert order_note == 'This is a test order for workflow testing'
        order_assignee = order['order_assignee']
        assert order_assignee == 'admin'
        
        # Get the order ID
        db_configs = app_client.application.config['db_configs']
        cursor = db_configs.conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE order_name = ?', ('Workflow Test Order',))
        order = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        order = dict(zip(columns, order))
        print(order)
        order_id = order['id']
        
        # Get order details
        get_order_response = app_client.get(f'/get_order_details/{order_id}')
        assert get_order_response.status_code == 200
        order_details = json.loads(get_order_response.data)
        print(order_details)
        assert order_details['order_name'] == 'Workflow Test Order'
        assert order_details['note'] == 'This is a test order for workflow testing'
        
        # Update order status
        update_status_response = app_client.post('/update_order_status', data={
            'order_id': order_id,
            'status': 'pending'
        })
        
        # Check that status was updated
        assert update_status_response.status_code == 200
        result = json.loads(update_status_response.data)
        assert result['success'] is True
        
        # Verify status was updated in database
        updated_order = operators.get_order_by_id(db_configs.conn, order_id)
        assert updated_order['status'] == 'pending'
        
        # Update the order details
        update_order_response = app_client.post('/update_order', data={
            'order_id': order_id,
            'order_name': 'Updated Workflow Order',
            'note': 'Updated description for workflow order',
            'order_assignee': 'admin',
            'quantity': 10,
            'link': 'https://www.google.com'
        })
        
        # Check that order was updated
        assert update_order_response.status_code == 200
        result = json.loads(update_order_response.data)
        print(result)
        assert result['success'] is True
        
        # Verify updates in database
        updated_order = operators.get_order_by_id(db_configs.conn, order_id)
        assert updated_order['order_name'] == 'Updated Workflow Order'
        assert updated_order['note'] == 'Updated description for workflow order'
        assert updated_order['order_assignee'] == 'admin'
        assert updated_order['quantity'] == 10
        assert updated_order['link'] == 'https://www.google.com'
        
        # Mark order as complete
        complete_response = app_client.post('/update_order_status', data={
            'order_id': order_id,
            'status': 'ordered'
        })
        
        # Check that status was updated
        assert complete_response.status_code == 200
        result = json.loads(complete_response.data)
        print(result)
        assert result['success'] is True
        
        # Verify status in database
        completed_order = operators.get_order_by_id(db_configs.conn, order_id)
        assert completed_order['status'] == 'ordered'
        
        # Delete the order
        delete_order_response = app_client.post('/delete_order', data={
            'order_id': order_id
        })
        
        # Check that order was deleted
        assert delete_order_response.status_code == 200
        result = json.loads(delete_order_response.data)
        assert result['success'] is True
        
        # Verify order was deleted from database
        deleted_order = operators.get_order_by_id(db_configs.conn, order_id)
        assert deleted_order is None
    
    def test_notification_workflow(self, app_client):
        """Test the complete notification workflow."""
        # Log in as admin using the helper method
        app_client.login()
        
        # Add a test notification via database
        db_configs = app_client.application.config['db_configs']
        operators.add_notification(
            db_configs.conn,
            'admin',
            'Workflow test notification',
            'admin',
            'order',
            reference_id=123
        )

        # check if the notification was added to the database
        notifications = operators.get_notifications(db_configs.conn, 'admin')
        print(notifications)
        assert len(notifications) == 1
        assert notifications[0]['message'] == 'Workflow test notification'
        
        # Go to notifications page
        notifications_response = app_client.get('/notifications')
        assert notifications_response.status_code == 200
        html = notifications_response.data.decode('utf-8')
        assert 'Workflow test notification' in html
        
        # Get the notification ID
        notifications = operators.get_notifications(db_configs.conn, 'admin')
        notification_id = next(n['id'] for n in notifications if n['message'] == 'Workflow test notification')
        
        # Mark notification as read
        mark_read_response = app_client.post('/api/notifications/mark-read', json={
            'id': notification_id
        })
        
        # Check that notification was marked as read
        assert mark_read_response.status_code == 200
        result = json.loads(mark_read_response.data)
        assert result['success'] is True
        
        # Verify in database
        updated_notifications = operators.get_notifications(db_configs.conn, 'admin')
        updated_notification = next(n for n in updated_notifications if n['id'] == notification_id)
        assert updated_notification['read'] == 1