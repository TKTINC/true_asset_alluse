"""
User Model

This module implements the User model for Flask-Login.
"""

from flask_login import UserMixin

class User(UserMixin):
    """
    User model for Flask-Login.
    """
    
    def __init__(self, id):
        self.id = id


