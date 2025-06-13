import os
from . import create_app, db
from .models import User
from getpass import getpass
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    username = input("Enter admin username: ")
    password = getpass("Enter admin password: ")

    if not User.query.filter_by(username=username).first():
        admin = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=True,
            insta_username=username
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created with username '{username}'.")
    else:
        print(f"User '{username}' already exists.")
