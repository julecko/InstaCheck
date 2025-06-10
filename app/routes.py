from flask import (
    current_app as app,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from .models import User, InstaBot, Scan
from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
import json
from instagrapi import Client
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    bots = InstaBot.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", bots=bots)

@app.route("/add_bot", methods=["POST"])
@login_required
def add_bot():
    username = request.form["username"]
    password = request.form["password"]
    if not username or not password:
        flash("Username and password required")
        return redirect(url_for("dashboard"))
    bot = InstaBot(username=username, password=password, user_id=current_user.id)
    db.session.add(bot)
    db.session.commit()
    flash("Instagram bot added!")
    return redirect(url_for("dashboard"))

@app.route("/scan/<int:bot_id>")
@login_required
def scan(bot_id):
    bot = InstaBot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    client = Client()
    try:
        client.login(bot.username, bot.password)
    except Exception as e:
        flash(f"Failed to login Instagram bot: {e}")
        return redirect(url_for("dashboard"))

    followers_after = client.user_followers(client.user_id_from_username(current_user.insta_username))
    follower_usernames_after = list(followers_after.keys())

    last_scan = Scan.query.filter_by(bot_id=bot.id, user_id=current_user.id).order_by(Scan.scan_time.desc()).first()
    followers_before = []
    if last_scan:
        followers_before = json.loads(last_scan.followers_after)

    scan_record = Scan(
        user_id=current_user.id,
        bot_id=bot.id,
        scan_time=datetime.utcnow(),
        followers_before=json.dumps(followers_before),
        followers_after=json.dumps(follower_usernames_after),
    )
    db.session.add(scan_record)
    db.session.commit()

    left = list(set(followers_before) - set(follower_usernames_after))
    stayed = list(set(follower_usernames_after) & set(followers_before))

    return render_template("scans.html", left=left, stayed=stayed, bot=bot)

@app.route("/scans")
@login_required
def scans():
    user_scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.scan_time.desc()).all()
    return render_template("scans.html", scans=user_scans)
