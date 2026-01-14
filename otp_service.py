import smtplib
import random
import os
from email.message import EmailMessage
from datetime import datetime, timedelta
import json

# In-memory OTP storage (for production, use Redis or database)
otp_storage = {}

def generate_otp():
    """Generate a random 6-digit OTP"""
    return str(random.randint(100000, 999999))

def store_otp(username, otp):
    """Store OTP with expiry time (10 minutes)"""
    expiry_time = datetime.now() + timedelta(minutes=10)
    otp_storage[username] = {
        'otp': otp,
        'expiry': expiry_time.isoformat(),
        'used': False
    }

def verify_otp(username, otp):
    """Verify OTP and check expiry"""
    if username not in otp_storage:
        return False, "No OTP found for this username"
    
    stored_data = otp_storage[username]
    
    # Check if already used
    if stored_data['used']:
        return False, "OTP has already been used"
    
    # Check expiry
    expiry_time = datetime.fromisoformat(stored_data['expiry'])
    if datetime.now() > expiry_time:
        del otp_storage[username]
        return False, "OTP has expired"
    
    # Check OTP match
    if stored_data['otp'] != otp:
        return False, "Invalid OTP"
    
    # Mark as used
    otp_storage[username]['used'] = True
    return True, "OTP verified successfully"

def invalidate_otp(username):
    """Invalidate OTP after password reset"""
    if username in otp_storage:
        del otp_storage[username]

def send_otp_email(recipient_email, username, otp):
    """Send OTP via Gmail SMTP"""
    try:
        # Get credentials from environment variables
        sender_email = os.getenv('JMI_EMAIL')
        sender_password = os.getenv('JMI_EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("ERROR: Email credentials not found in environment variables")
            return False, "Email service not configured"
        
        # Create email message
        msg = EmailMessage()
        msg['Subject'] = 'JMIConnect - Password Reset OTP'
        msg['From'] = f'JMIConnect <{sender_email}>'
        msg['To'] = recipient_email
        
        # Email body with professional HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #10b981, #065f46); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 800; }}
                .content {{ padding: 40px 30px; }}
                .otp-box {{ background: #f1f5f9; border-left: 4px solid #10b981; padding: 20px; margin: 25px 0; border-radius: 8px; }}
                .otp-code {{ font-size: 36px; font-weight: 800; color: #065f46; letter-spacing: 8px; text-align: center; margin: 10px 0; }}
                .warning {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 8px; color: #991b1b; font-size: 14px; }}
                .footer {{ background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 13px; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <p style="font-size: 16px; color: #1f2937;">Hello <strong>{username}</strong>,</p>
                    <p style="color: #6b7280;">We received a request to reset your password for your JMIConnect account. Use the OTP below to proceed:</p>
                    
                    <div class="otp-box">
                        <p style="margin: 0; color: #475569; font-size: 14px; text-align: center;">Your One-Time Password</p>
                        <div class="otp-code">{otp}</div>
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-align: center;">Valid for 10 minutes</p>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        • Never share this OTP with anyone<br>
                        • JMIConnect will never ask for your password via email<br>
                        • If you didn't request this, please ignore this email
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px;">This OTP will expire in <strong>10 minutes</strong> and can only be used once.</p>
                </div>
                <div class="footer">
                    <p style="margin: 0;">© 2026 JMIConnect | Jamia Millia Islamia</p>
                    <p style="margin: 5px 0 0 0;">This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.set_content("Your OTP for password reset is: " + otp)
        msg.add_alternative(html_content, subtype='html')
        
        # Send email via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        
        print(f"OTP email sent successfully to {recipient_email}")
        return True, "OTP sent successfully"
        
    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP Authentication failed. Check email credentials.")
        return False, "Email authentication failed"
    except smtplib.SMTPException as e:
        print(f"ERROR: SMTP error occurred: {str(e)}")
        return False, "Failed to send email"
    except Exception as e:
        print(f"ERROR: Unexpected error sending email: {str(e)}")
        return False, "An error occurred while sending email"
