import os
from flask import Flask

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-fallback-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # register blueprints
    from auth.routes import auth_bp
    from api.routes import api_bp
    from features.routes import features_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(features_bp)

    return app