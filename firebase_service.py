import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime

# Path to service account key
SERVICE_ACCOUNT_KEY = 'serviceAccountKey.json'

import json

def init_firebase():
    if not firebase_admin._apps:
        # 1. Try file
        if os.path.exists(SERVICE_ACCOUNT_KEY):
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
        # 2. Try Environment Variable (JSON String)
        elif os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
            try:
                service_account_info = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Error initializing Firebase from env var: {e}")
                return None
        # 3. Default (ADC)
        else:
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                print(f"Warning: Firebase initialization failed. {e}")
                return None
    return firestore.client()

db = init_firebase()

def get_db():
    global db
    if db is None:
        db = init_firebase()
    return db

# --- Announcements ---
def get_announcements(section=None):
    client = get_db()
    if client is None: return []
    
    query = client.collection('announcements')
    if section:
        query = query.where('section', '==', section)
    
    docs = query.stream()
    res = [doc.to_dict() | {'id': doc.id} for doc in docs]
    # Sort in memory to avoid needing a composite index
    res.sort(key=lambda x: x.get('date', ''), reverse=True)
    return res

def add_announcement(data):
    client = get_db()
    if client is None: return None
    
    _, doc_ref = client.collection('announcements').add(data)
    return doc_ref.id

def delete_announcement(item_id):
    client = get_db()
    if client is None: return False
    
    client.collection('announcements').document(item_id).delete()
    return True

# --- Notes ---
def get_notes(section=None):
    client = get_db()
    if client is None: return []
    
    query = client.collection('notes')
    if section:
        query = query.where('section', '==', section)
    
    docs = query.stream()
    res = [doc.to_dict() | {'id': doc.id} for doc in docs]
    # Sort in memory
    res.sort(key=lambda x: x.get('date', ''), reverse=True)
    return res

def add_note(data):
    """
    Saves note metadata to Firestore. 
    Expects 'download_url' to be present in data.
    """
    client = get_db()
    if client is None: return None
    
    # Save metadata to Firestore
    _, doc_ref = client.collection('notes').add(data)
    return doc_ref.id

def delete_note(note_id):
    """
    Deletes note metadata from Firestore.
    Does NOT manage file deletion as files are hosted externally.
    """
    client = get_db()
    if client is None: return False
    
    client.collection('notes').document(note_id).delete()
    return True

# --- Contacts ---
def get_contacts(section=None):
    client = get_db()
    if client is None: return []
    
    query = client.collection('contacts')
    if section:
        query = query.where('section', '==', section)
    
    docs = query.stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

def add_contact(data):
    client = get_db()
    if client is None: return None
    
    _, doc_ref = client.collection('contacts').add(data)
    return doc_ref.id

def delete_contact(contact_id):
    client = get_db()
    if client is None: return False
    
    client.collection('contacts').document(contact_id).delete()
    return True

# --- Users ---
def get_user(username):
    client = get_db()
    if client is None: return None
    
    # Try username as document ID first
    doc = client.collection('users').document(username).get()
    if doc.exists:
        return doc.to_dict()
    
    # Otherwise search by email
    docs = client.collection('users').where('email', '==', username).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None

def update_user(username, data):
    client = get_db()
    if client is None: return False
    
    client.collection('users').document(username).set(data, merge=True)
    return True

# --- Sessions ---
def get_session(session_id):
    client = get_db()
    if client is None: return None
    
    docs = client.collection('sessions').where('session_id', '==', session_id).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None

def create_session(session_data):
    client = get_db()
    if client is None: return None
    
    # One session per username for simplicity
    client.collection('sessions').document(session_data['username']).set(session_data)
    return True

def delete_session(session_id):
    client = get_db()
    if client is None: return False
    
    docs = client.collection('sessions').where('session_id', '==', session_id).stream()
    for doc in docs:
        doc.reference.delete()
    return True
