from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # register blueprints
    from auth.routes import auth_bp
    from api.routes import api_bp
    from features.routes import features_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(features_bp)

    return app