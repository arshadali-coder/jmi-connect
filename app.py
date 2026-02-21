from dotenv import load_dotenv
from extensions import create_app
from flask import render_template, request, redirect, url_for
from utils import get_current_user

# Load environment variables
load_dotenv()

app = create_app()

from features.cr_routes import cr_bp
app.register_blueprint(cr_bp)

from auth.password_reset import password_reset_bp
app.register_blueprint(password_reset_bp)

@app.route('/')
def index():
    user = get_current_user()
    if user:
        if user.get('role') == 'cr':
            return redirect(url_for('cr.dashboard'))
        return redirect(url_for('features.notes'))
    return render_template("login.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)