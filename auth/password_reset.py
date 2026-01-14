from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import firebase_service as fb
import otp_service
from werkzeug.security import generate_password_hash

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/password-reset')

@password_reset_bp.route('/request', methods=['GET', 'POST'])
def request_otp():
    """Step 1: Request OTP for password reset"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'success': False, 'message': 'Username is required'}), 400
        
        # Check if user exists
        user = fb.get_user(username)
        if not user:
            # Don't reveal if user exists or not (security)
            return jsonify({'success': True, 'message': 'If this username exists, an OTP has been sent to the registered email'})
        
        # Check if user has email
        email = user.get('email')
        if not email:
            return jsonify({'success': False, 'message': 'No email associated with this account. Please contact your CR.'}), 400
        
        # Generate and send OTP
        otp = otp_service.generate_otp()
        otp_service.store_otp(username, otp)
        
        success, message = otp_service.send_otp_email(email, username, otp)
        
        if success:
            return jsonify({'success': True, 'message': 'OTP has been sent to your registered email address'})
        else:
            return jsonify({'success': False, 'message': message}), 500
    
    return render_template('password_reset/request_otp.html')

@password_reset_bp.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    """Step 2: Verify OTP"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        otp = data.get('otp', '').strip()
        
        if not username or not otp:
            return jsonify({'success': False, 'message': 'Username and OTP are required'}), 400
        
        # Verify OTP
        valid, message = otp_service.verify_otp(username, otp)
        
        if valid:
            return jsonify({'success': True, 'message': 'OTP verified successfully'})
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    return render_template('password_reset/verify_otp.html')

@password_reset_bp.route('/reset', methods=['GET', 'POST'])
def reset_password():
    """Step 3: Reset password after OTP verification"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not username or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Validate password
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        # Verify OTP was verified (check if it exists and is marked as used)
        if username not in otp_service.otp_storage or not otp_service.otp_storage[username].get('used'):
            return jsonify({'success': False, 'message': 'Please verify OTP first'}), 400
        
        # Get user
        user = fb.get_user(username)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Update password (hash it)
        hashed_password = generate_password_hash(new_password)
        user['password'] = hashed_password
        
        # Update user in database
        success = fb.update_user(username, {'password': hashed_password})
        
        if success:
            # Invalidate OTP
            otp_service.invalidate_otp(username)
            return jsonify({'success': True, 'message': 'Password reset successful. You can now login with your new password.'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update password. Please try again.'}), 500
    
    return render_template('password_reset/reset_password.html')
