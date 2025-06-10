import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    load_dotenv()

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://"
        f"{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    with app.app_context():
        from . import routes, models
        db.create_all()

    return app
