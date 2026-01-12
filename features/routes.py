import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app

features_bp = Blueprint('features', __name__)

def get_current_user():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None
    return fb.get_session(session_id)

def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

import firebase_service as fb

# ==================== NOTES (Student View) ====================
@features_bp.route('/notes')
def notes():
    user = get_current_user()
    if not user:
        return redirect(url_for('index'))
    
    section = user.get('section')
    # Fetch from Firebase
    section_notes = fb.get_notes(section)
    
    # Group by semester for better organization
    semesters = {}
    for note in section_notes:
        sem = note.get('semester', 'Unknown')
        if sem not in semesters:
            semesters[sem] = []
        semesters[sem].append(note)
            
    return render_template("notes.html", user=user, notes=section_notes, semesters=semesters)

# ==================== ANNOUNCEMENTS (Student View) ====================
@features_bp.route('/announcements')
def announcements():
    user = get_current_user()
    if not user:
        return redirect(url_for('index'))
    
    section = user.get('section')
    # Fetch from Firebase
    section_announcements = fb.get_announcements(section)
                
    return render_template("announcements.html", user=user, announcements=section_announcements)

# ==================== CR CONNECT (Student View) ====================
@features_bp.route('/cr-connect')
def cr_connect():
    user = get_current_user()
    if not user:
        return redirect(url_for('index'))
    
    # Load Firebase config (still used for frontend RTC if needed)
    firebase_config = None
    try:
        from firebase_config import FIREBASE_CONFIG
        firebase_config = FIREBASE_CONFIG
    except:
        pass
        
    return render_template("cr-connect.html", user=user, firebase_config=firebase_config)

# ==================== EMERGENCY CONTACTS (Student View) ====================
@features_bp.route('/emergency-contacts')
def emergency_contacts():
    user = get_current_user()
    if not user:
        return redirect(url_for('index'))
        
    section = user.get('section')
    # Fetch from Firebase
    section_contacts = fb.get_contacts(section)
            
    return render_template("emergency-contacts.html", user=user, contacts=section_contacts)
