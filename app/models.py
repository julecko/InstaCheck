from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    insta_username = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bots = db.relationship("InstaBot", backref="owner", lazy=True)
    scans = db.relationship("Scan", backref="user", lazy=True)

class InstaBot(db.Model):
    __tablename__ = "insta_bots"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scans = db.relationship("Scan", backref="bot", lazy=True)

class Scan(db.Model):
    __tablename__ = "scans"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey("insta_bots.id"), nullable=False)
    scan_time = db.Column(db.DateTime, default=datetime.utcnow)
    followers_before = db.Column(db.Text)
    followers_after = db.Column(db.Text)
