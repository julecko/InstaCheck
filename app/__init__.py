from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

logging.basicConfig(level=logging.ERROR)

def create_app():
    app = Flask(__name__)
    
    env_path = Path(__file__).parent.parent / '.env'  # adjust path relative to this file
    load_dotenv(dotenv_path=env_path)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://"
        f"{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.scans import scans_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scans_bp)

    return app
