import json
import os
from extensions import create_app
from flask import render_template, request, redirect, url_for

app = create_app()

from features.cr_routes import cr_bp
app.register_blueprint(cr_bp)


import firebase_service as fb

def get_current_user():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None
    return fb.get_session(session_id)

@app.route('/')
def index():
    user = get_current_user()
    if user:
        if user.get('role') == 'cr':
            return redirect(url_for('cr.dashboard'))
        return redirect(url_for('features.notes'))
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)