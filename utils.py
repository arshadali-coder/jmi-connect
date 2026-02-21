"""
JMIConnect - Shared Utilities
Common helper functions used across multiple blueprints.
"""
from flask import request
import firebase_service as fb


def get_current_user():
    """Get the currently logged-in user from session cookie."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None
    return fb.get_session(session_id)
