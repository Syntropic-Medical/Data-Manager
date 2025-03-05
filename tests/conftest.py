"""
Configuration and fixtures for pytest.
"""
import os
import sys
import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
import importlib.util

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(os.path.join(project_root, 'src', 'utils'))
sys.path.append(os.path.join(project_root, 'src', 'database'))
sys.path.append(os.path.join(project_root, 'src', 'web'))

# Patch werkzeug to handle the __version__ attribute missing in newer versions
import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '2.2.3'  # Use a compatible version for test compatibility

# Import necessary modules
from src.database import operators, configs
from src.utils import utils

@pytest.fixture
def db_config():
    """Create a test database configuration with an in-memory SQLite database."""
    class TestConfig:
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.db_file = ':memory:'
            # Add table_lists attribute to match what init_db expects
            self.table_lists = [
                """ CREATE TABLE IF NOT EXISTS entries (
                                        id_hash text NOT NULL,
                                        tags text,
                                        extra_txt text,
                                        file_path text,
                                        date DATETIME NOT NULL,
                                        author text NOT NULL,
                                        conditions text,
                                        entry_name text,
                                        entry_parent text,
                                        id integer primary key autoincrement
                                    ); """, 
                """ CREATE TABLE IF NOT EXISTS tags (
                                        tag text NOT NULL,
                                        id integer primary key autoincrement
                                    ); """,
                """ CREATE TABLE IF NOT EXISTS conditions (
                                        condition text NOT NULL,
                                        id integer primary key autoincrement
                                    ); """,
                """ CREATE TABLE IF NOT EXISTS authors (
                                        author text NOT NULL,
                                        id integer primary key autoincrement
                                    ); """,
                """ CREATE TABLE IF NOT EXISTS users (
                                        username text NOT NULL unique,
                                        password text NOT NULL default 'admin',
                                        admin bool NOT NULL default 0,
                                        order_manager bool NOT NULL default 0,
                                        name text,
                                        email text,
                                        email_enabled bool NOT NULL default 1,
                                        id integer primary key autoincrement
                                    ); """,
                """ CREATE TABLE IF NOT EXISTS orders (
                                        id integer primary key autoincrement,
                                        order_name text NOT NULL,
                                        link text,
                                        quantity integer NOT NULL,
                                        note text,
                                        order_assignee text NOT NULL,
                                        order_author text NOT NULL,
                                        status text NOT NULL,
                                        date DATETIME NOT NULL
                                    ); """,
                """ CREATE TABLE IF NOT EXISTS notifications (
                                        id integer primary key autoincrement,
                                        author text NOT NULL,
                                        message text NOT NULL,
                                        destination text NOT NULL,
                                        date text NOT NULL,
                                        read integer DEFAULT 0,
                                        type text NOT NULL,
                                        reference_id integer
                                    ); """,
                """ CREATE TABLE IF NOT EXISTS password_resets (
                                        username TEXT NOT NULL,
                                        token TEXT PRIMARY KEY,
                                        expiry TEXT,
                                        used INTEGER DEFAULT 0
                                    ); """
            ]
    
    config = TestConfig()
    
    # Create required tables
    utils.init_db(config)
    
    yield config
    
    # Clean up
    config.conn.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def app_client():
    """Create a test Flask client for API testing."""
    import flask
    from src.web.api import WebApp
    
    # Create a test configuration - Fix the way we create this
    db_configs = configs.database_configs()
    # Override the default db name to use in-memory SQLite
    db_configs.dbName = ':memory:'
    db_configs.make_conn()
    
    # Initialize the database
    utils.init_db(db_configs)
    
    # Create a test app
    webapp = WebApp(
        db_configs=db_configs,
        ip='localhost',
        port=5000,
        static_folder='web',
        recaptcha_bool=False,
        num_threads=1,
        mailing_bool=False,
        host_url='http://localhost:5000'
    )
    
    # Configure app for testing
    webapp.app.config['TESTING'] = True
    webapp.app.config['WTF_CSRF_ENABLED'] = False
    webapp.app.config['SECRET_KEY'] = 'test-key'
    webapp.app.config['db_configs'] = db_configs  # Store db_configs in app.config for tests
    webapp.app.config['conn'] = db_configs.conn  # Store conn directly in app.config for tests
    webapp.app.config['SERVER_NAME'] = 'localhost'  # Required for url_for to work in tests
    webapp.app.config['USERNAME'] = 'admin'  # Set default username for tests
    
    # Register routes (won't start the server in testing mode)
    webapp.run()
    
    # Create a test client
    client = webapp.app.test_client()
    
    # Enable session handling in the test client
    client.testing = True
    client.preserve_context_on_exception = False
    
    # Add a test admin user
    operators.add_user(
        db_configs.conn, 
        'admin', 
        'admin123', 
        1, 
        1, 
        'Test Admin', 
        'admin@example.com'
    )
    
    # Helper function to log in the test client
    def login(username='admin', password='admin123'):
        # First try to log in through the actual login endpoint
        response = client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
        
        # Manually set up the session to ensure it works
        with client.session_transaction() as sess:
            sess['username'] = username
            sess['admin'] = True
            sess['order_manager'] = True
            sess['logged_in'] = True
        
        return response
    
    # Attach the login helper to the client
    client.login = login
    
    # Set up an application context
    with webapp.app.app_context():
        yield client 