from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

import firebase_service as fb
from utils import get_current_user

cr_bp = Blueprint('cr', __name__, url_prefix='/cr')


def cr_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('index'))
        
        full_user = fb.get_user(user['username'])
        
        if not full_user or full_user.get('role') != 'cr':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper


# ==================== DASHBOARD ====================
@cr_bp.route('/dashboard')
@cr_required
def dashboard():
    user = get_current_user()
    section = user.get('section')
    
    # Get stats from Firebase
    announcements_list = fb.get_announcements(section)
    notes_list = fb.get_notes(section)
    contacts_list = fb.get_contacts(section)
    
    stats = {
        'announcements': len(announcements_list),
        'notes': len(notes_list),
        'contacts': len(contacts_list)
    }
    
    return render_template('cr_panel/dashboard.html', user=user, stats=stats)

# ==================== ANNOUNCEMENTS ====================
@cr_bp.route('/announcements', methods=['GET', 'POST'])
@cr_required
def announcements():
    user = get_current_user()
    section = user.get('section')

    if request.method == 'POST':
        link = request.form.get('link', '').strip()
        
        new_item = {
            "title": request.form.get('title'),
            "subtitle": request.form.get('type').title(),  # Use type as subtitle (e.g., "Announcement", "Deadline")
            "description": request.form.get('description'),
            "type": request.form.get('type'),
            "date": request.form.get('date') or datetime.now().strftime('%Y-%m-%d'),
            "section": section,
            "created_by": user['username'],
            "timestamp": datetime.now().isoformat()
        }
        
        # Only add link if provided
        if link:
            new_item["link"] = link
            new_item["link_text"] = "View Details"
        
        fb.add_announcement(new_item)
        flash("Announcement published successfully!", "success")
        return redirect(url_for('cr.announcements'))

    # Fetch from Firebase
    section_data = fb.get_announcements(section)
    return render_template('cr_panel/announcements.html', user=user, announcements=section_data)

@cr_bp.route('/announcements/delete/<item_id>', methods=['POST'])
@cr_required
def delete_announcement(item_id):
    fb.delete_announcement(item_id)
    flash("Item deleted successfully.", "success")
    return redirect(url_for('cr.announcements'))

# ==================== NOTES ====================
@cr_bp.route('/notes', methods=['GET', 'POST'])
@cr_required
def notes():
    user = get_current_user()
    section = user.get('section')

    if request.method == 'POST':
        download_url = request.form.get('download_url')
        if not download_url:
            flash("Download URL is required.", "error")
            return redirect(request.url)
        
        # Basic validation
        if not download_url.startswith(('http://', 'https://')):
             flash("Please enter a valid URL starting with http:// or https://", "warning")
             return redirect(request.url)

        new_note = {
            "subject": request.form.get('subject'),
            "semester": request.form.get('semester'),
            "download_url": download_url,
            "filename": "Drive Link", 
            "original_name": "External Resource",
            "uploaded_by": user['username'],
            "section": section,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save metadata to Firestore (No file upload)
        fb.add_note(new_note)
        
        flash("Note resource added successfully!", "success")
        return redirect(url_for('cr.notes'))

    # Fetch from Firebase
    section_data = fb.get_notes(section)
    return render_template('cr_panel/notes.html', user=user, notes=section_data)

@cr_bp.route('/notes/delete/<note_id>', methods=['POST'])
@cr_required
def delete_note(note_id):
    # Only delete metadata from Firestore
    fb.delete_note(note_id)
    flash("Resource removed successfully.", "success")
    return redirect(url_for('cr.notes'))

# ==================== CONTACTS ====================
@cr_bp.route('/contacts', methods=['GET', 'POST'])
@cr_required
def contacts():
    user = get_current_user()
    section = user.get('section')

    if request.method == 'POST':
        new_contact = {
            "name": request.form.get('name'),
            "role": request.form.get('role'),
            "phone": request.form.get('phone'),
            "section": section,
            "created_by": user['username']
        }
        fb.add_contact(new_contact)
        flash("Contact added successfully!", "success")
        return redirect(url_for('cr.contacts'))

    section_data = fb.get_contacts(section)
    return render_template('cr_panel/contacts.html', user=user, contacts=section_data)

@cr_bp.route('/contacts/delete/<contact_id>', methods=['POST'])
@cr_required
def delete_contact(contact_id):
    fb.delete_contact(contact_id)
    flash("Contact removed successfully.", "success")
    return redirect(url_for('cr.contacts'))

# ==================== MESSAGES (Firebase-powered) ====================
@cr_bp.route('/messages')
@cr_required
def messages():
    user = get_current_user()
    
    # Load Firebase config
    firebase_config = None
    try:
        from firebase_config import FIREBASE_CONFIG
        firebase_config = FIREBASE_CONFIG
    except (ImportError, ModuleNotFoundError):
        pass
        
    return render_template('cr_panel/messages.html', user=user, firebase_config=firebase_config)
