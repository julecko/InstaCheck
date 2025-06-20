from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import InstaBot, Scan
from .. import db
import json
from instagrapi import Client
from datetime import datetime
import logging

scans_bp = Blueprint('scans', __name__)
logger = logging.getLogger(__name__)

@scans_bp.route("/scan", methods=["POST"])
@login_required
def scan():
    bot_id = request.form.get("bot_id")
    bot = InstaBot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    if not current_user.insta_username:
        flash("Please set your Instagram username in your profile", "error")
        return redirect(url_for("dashboard.edit_profile"))

    client = Client()
    debug_info = []

    try:
        client.login(bot.username, bot.password)
        debug_info.append("Login successful")
    except Exception as e:
        debug_info.append(f"Login failed for bot {bot.username}: {str(e)}")
        logger.error(f"Login failed for bot {bot_id}: {str(e)}")
        flash(f"Failed to login Instagram bot: {e}", "error")
        return redirect(url_for("dashboard.dashboard"))

    try:
        followers_after = client.user_followers(client.user_id_from_username(current_user.insta_username))
        follower_usernames_after = list(map(lambda x: x.username, followers_after.values()))
        debug_info.append("Retrieved followers")
    except Exception as e:
        debug_info.append(f"Failed to retrieve followers: {str(e)}")
        logger.error(f"Failed to retrieve followers for {current_user.insta_username}: {str(e)}")
        flash(f"Failed to scan followers: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard"))

    last_scan = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.scan_time.desc()).first()
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
        logger.error(f"Failed to save scan record for user {current_user.id}: {str(e)}")
        flash(f"Failed to save scan data: {e}", "error")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("scans.html", left=left, stayed=stayed, new_followers=new_followers, bot=bot, debug_info=debug_info)

@scans_bp.route("/scan_history")
@login_required
def scan_history():
    scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.scan_time.desc()).all()
    for scan in scans:
        followers_before = json.loads(scan.followers_before)
        followers_after = json.loads(scan.followers_after)
        scan.left = list(set(followers_before) - set(followers_after))
        scan.stayed = list(set(followers_after) & set(followers_before))
        scan.new_followers = list(set(followers_after) - set(followers_before))
    return render_template("scan_history.html", scans=scans)

@scans_bp.route("/scan_detail/<int:scan_id>")
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