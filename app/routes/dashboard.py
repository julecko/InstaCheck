from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import User, InstaBot
from .. import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    bots = InstaBot.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", bots=bots)

@dashboard_bp.route("/add_bot", methods=["POST"])
@login_required
def add_bot():
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        flash("Username and password required", "error")
        return redirect(url_for("dashboard.dashboard"))
    bot = InstaBot(username=username, password=password, user_id=current_user.id)
    db.session.add(bot)
    db.session.commit()
    flash("Instagram bot added!", "success")
    return redirect(url_for("dashboard.dashboard"))

@dashboard_bp.route("/edit_profile", methods=["GET", "POST"])
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
                return redirect(url_for("dashboard.edit_profile"))
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
            return redirect(url_for("dashboard.edit_profile"))
        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", "error")
            return redirect(url_for("dashboard.edit_profile"))
    return render_template("edit_profile.html", user=current_user)