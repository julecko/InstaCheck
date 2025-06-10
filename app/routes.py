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
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

@app.route("/scans")
@login_required
def scans():
    user_scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.scan_time.desc()).all()
    return render_template("scans.html", scans=user_scans)

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        insta_username = request.form.get("insta_username", "").strip()
        
        changes_made = False
        
        if username and username != current_user.username:
            existing_user = User.query.filter(User.username == username, User.id != current_user.id).first()
            if existing_user:
                flash("Username already taken", "error")
                return redirect(url_for("edit_profile"))
            current_user.username = username
            changes_made = True
        
        if password:
            current_user.password = generate_password_hash(password, method="pbkdf2:sha256")
            changes_made = True
        
        if insta_username and insta_username != current_user.insta_username:
            current_user.insta_username = insta_username
            changes_made = True
        
        if not changes_made:
            flash("No changes provided", "info")
            return redirect(url_for("edit_profile"))
        
        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", "error")
            return redirect(url_for("edit_profile"))
    
    return render_template("edit_profile.html", user=current_user)

@app.route("/scan/<int:bot_id>")
@login_required
def scan(bot_id):
    bot = InstaBot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    client = Client()
    debug_info = []
    
    try:
        client.login(bot.username, bot.password)
        debug_info.append("Login successful")
    except Exception as e:
        debug_info.append(f"Login failed: {str(e)}")
        logger.error("Login failed for bot %s: %s", bot.username, str(e))
        flash(f"Failed to login Instagram bot: {e}", "error")
        return redirect(url_for("dashboard"))

    try:
        followers_after = client.user_followers(client.user_id_from_username(current_user.insta_username))
        follower_usernames_after = list(map(lambda x: x.username, followers_after.values()))
        debug_info.append(f"Retrieved followers")
    except Exception as e:
        debug_info.append(f"Failed to retrieve followers: {str(e)}")
        logger.error("Failed to retrieve followers for %s: %s", current_user.insta_username, str(e))
        flash(f"Failed to scan followers: {e}", "error")
        return redirect(url_for("dashboard"))

    last_scan = Scan.query.filter_by(bot_id=bot.id, user_id=current_user.id).order_by(Scan.scan_time.desc()).first()
    followers_before = []
    if last_scan:
        followers_before = json.loads(last_scan.followers_after)
        debug_info.append("Loaded previous scan data")

    left = list(set(followers_before) - set(follower_usernames_after))
    stayed = list(set(follower_usernames_after) & set(followers_before))
    new_followers = list(set(follower_usernames_after) - set(followers_before))

    if left:
        logger.error("Users who left: %s", ", ".join(left))
    if stayed:
        logger.error("Users who stayed: %s", ", ".join(stayed))
    if new_followers:
        logger.error("New followers: %s", ", ".join(new_followers))

    # Create scan record
    scan_record = Scan(
        user_id=current_user.id,
        bot_id=bot.id,
        scan_time=datetime.utcnow(),
        followers_before=json.dumps(followers_before),
        followers_after=json.dumps(follower_usernames_after),
        debug_info="\n".join(debug_info)
    )
    try:
        db.session.add(scan_record)
        db.session.commit()
    except Exception as e:
        logger.error("Failed to save scan record for bot %s: %s", bot.id, str(e))
        flash(f"Failed to save scan data: {e}", "error")
        return redirect(url_for("dashboard"))

    return render_template("scans.html", left=left, stayed=stayed, new_followers=new_followers, bot=bot, debug_info=debug_info)

@app.route("/scan_history/<int:bot_id>")
@login_required
def scan_history(bot_id):
    bot = InstaBot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    scans = Scan.query.filter_by(bot_id=bot.id, user_id=current_user.id).order_by(Scan.scan_time.desc()).all()
    for scan in scans:
        followers_before = json.loads(scan.followers_before)
        followers_after = json.loads(scan.followers_after)
        scan.left = list(set(followers_before) - set(followers_after))
        scan.stayed = list(set(followers_after) & set(followers_before))
        scan.new_followers = list(set(followers_after) - set(followers_before))
    return render_template("scan_history.html", bot=bot, scans=scans)

@app.route("/scan_detail/<int:scan_id>")
@login_required
def scan_detail(scan_id):
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    bot = InstaBot.query.get_or_404(scan.bot_id)
    followers_before = json.loads(scan.followers_before)
    followers_after = json.loads(scan.followers_after)
    left = list(set(followers_before) - set(followers_after))
    stayed = list(set(followers_after) & set(followers_before))
    new_followers = list(set(followers_after) - set(followers_before))
    debug_info = scan.debug_info.split("\n") if scan.debug_info else []
    return render_template("scan_detail.html", scan=scan, bot=bot, left=left, stayed=stayed, new_followers=new_followers, debug_info=debug_info)