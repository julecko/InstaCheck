import os
from . import create_app, db
from .models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password=generate_password_hash("admin"),
            is_admin=True,
            insta_username="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created with username 'admin' and password 'admin'.")
    else:
        print("Admin user already exists.")
