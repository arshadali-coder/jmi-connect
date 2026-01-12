import json
import os
import uuid
from flask import Blueprint, jsonify, request, make_response, render_template, current_app, flash, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_path(filename):
    return os.path.join(current_app.root_path, 'database', filename)


def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

import firebase_service as fb

def get_current_user():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None
    return fb.get_session(session_id)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = fb.get_user(username)

    if user and user.get('password') == password:
        # Create session
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "username": user['username'],
            "email": user['email'],
            "section": user.get('section', ''),
            "branch": user.get('branch', ''),
            "mobile": user.get('mobile', ''),
            "profile_pic": user.get('profile_pic', ''),
            "role": user.get('role', 'student'),
            "timestamp": datetime.now().isoformat()
        }
        
        fb.create_session(session_data)

        # Determine redirect based on role
        redirect_url = url_for('cr.dashboard') if user.get('role') == 'cr' else url_for('features.notes')
        res = make_response(jsonify({"status": "success", "message": "Login successful", "user": session_data, "redirect": redirect_url}))
        res.set_cookie('session_id', session_id, httponly=True, max_age=3600*24*7) # 1 week
        return res
    
    return jsonify({"status": "error", "message": "Invalid username or password"}), 401

@auth_bp.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        fb.delete_session(session_id)
    
    res = make_response(jsonify({"status": "success", "message": "Logged out"}))
    res.set_cookie('session_id', '', expires=0)
    return res

@auth_bp.route('/session', methods=['GET'])
def get_session():
    session = get_current_user()
    if session:
        return jsonify({"status": "success", "user": session})
    return jsonify({"status": "error", "message": "Invalid session"}), 401

@auth_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    session_user = get_current_user()
    if not session_user:
        return redirect(url_for('index'))

    user = fb.get_user(session_user['username'])
    if not user:
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        # Profile Pic Upload Disabled due to Storage Migration
        
        if email: user['email'] = email
        if mobile: user['mobile'] = mobile

        # Password Change
        pw_changed = False
        if new_pw:
            if not current_pw:
                flash("Enter current password to set a new one.", "error")
            elif user['password'] != current_pw:
                flash("Incorrect current password.", "error")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "error")
            elif len(new_pw) < 6:
                flash("Password must be at least 6 characters.", "error")
            else:
                user['password'] = new_pw
                pw_changed = True
                flash("Password updated successfully.", "success")
        
        if not new_pw or (new_pw and pw_changed):
             if not new_pw: flash("Profile updated successfully.", "success")
        
        # Save to Firestore
        fb.update_user(user['username'], user)

        # Update Session in Firestore
        session_user['email'] = user.get('email')
        session_user['mobile'] = user.get('mobile')
        session_user['profile_pic'] = user.get('profile_pic')
        fb.create_session(session_user)

        return redirect(url_for('auth.settings'))

    return render_template('settings.html', user=user)
