import flask
from functools import wraps
import hashlib
import os

def check_logged_in(session):
    if 'logged_in' in session:
        if session['logged_in']:
            return True
    return False

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin' in flask.session:
            if flask.session['admin']:
                return f(*args, **kwargs)
            else:
                flask.flash('You need to login first.')
                return flask.redirect(flask.url_for('login'))
        else:
            flask.flash('You need to login first.')
            return flask.redirect(flask.url_for('login'))
    return wrap

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in flask.session:
            if flask.session['logged_in']:
                return f(*args, **kwargs)
            else:
                flask.flash('You need to login first.')
                return flask.redirect(flask.url_for('login'))
        else:
            flask.flash('You need to login first.')
            return flask.redirect(flask.url_for('login'))
    return wrap

def hash_password(password):
    """Hash a password with a random salt using SHA-256"""
    salt = os.urandom(32)  # 32 bytes = 256 bits
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',  # Hash algorithm
        password.encode('utf-8'),  # Convert password to bytes
        salt,  # Salt
        100000,  # Number of iterations
    )
    # Store salt and hash together
    return salt.hex() + ':' + hash_obj.hex()

def verify_password(stored_password, provided_password):
    """Verify a password against its hash"""
    if not stored_password or ':' not in stored_password:
        # Handle legacy plain text passwords
        return stored_password == provided_password
        
    salt_hex, hash_hex = stored_password.split(':')
    salt = bytes.fromhex(salt_hex)
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000,
    )
    return hash_obj.hex() == hash_hex