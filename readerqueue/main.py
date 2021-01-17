from flask import (
    render_template,
    redirect,
    url_for,
    request,
    session,
    Blueprint,
    current_app,
    flash,
)
from flask_login import logout_user, login_required, current_user
from readerqueue.models import Asset, AssetSkip, AssetTag, User
import httpx
import random
from datetime import datetime
from sqlalchemy import func
import maya
import math
from . import db


main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
    return render_template("index.html")


@main.route("/link/sync")
@login_required
def sync():
    pinboard_auth = current_user.pinboard_auth
    links = httpx.get(
        f"https://api.pinboard.in/v1/posts/all?auth_token={pinboard_auth}&format=json&meta=1"
    ).json()
    for link in links:
        id_ = link["hash"]
        asset = (
            db.session.query(Asset)
            .filter(Asset.upstream_id == id_)
            .filter(User.id == current_user.id)
            .one_or_none()
        )
        if asset is None:
            asset = build_new_asset(link)
            current_user.assets.append(asset)
            db.session.add(current_user)
        if asset.change_hash != link["meta"]:
            update_tags(asset, link["tags"])
    db.session.commit()
    return redirect(url_for("main.suggested_link"))


@main.route("/link/suggested")
@login_required
def suggested_link():
    query = (
        db.session.query(Asset, Asset.pinboard_created_at, func.count(AssetSkip.id))
        .filter(Asset.read_at == None)
        .filter(Asset.user_id == current_user.id)
        .outerjoin(AssetSkip)
        .group_by(Asset.id)
        .having(func.count(1) < 3)
    )
    tag_filter = session.get("tag_filter")
    if tag_filter is not None and tag_filter != "all":
        query = query.join(AssetTag).filter(AssetTag.tag == tag_filter)
    result = query.all()
    assets, created_at, skips = list(zip(*result))
    days_passed_ln = [
        math.log((datetime.utcnow() - d).total_seconds()) for d in created_at
    ]
    days_passed_adj = [d + s for d, s in zip(days_passed_ln, skips)]
    if len(days_passed_adj) > 1:
        max_score = max(*days_passed_adj) + 0.1
    else:
        max_score = days_passed_adj[0] + 0.1
    weights = [max_score - x for x in days_passed_adj]
    asset = random.choices(assets, k=1, weights=weights)[0]
    return render_template("suggested_link.html", asset=asset)


@main.route("/link/<link_id>/skip", methods=["POST"])
@login_required
def skip_link(link_id):
    asset = db.session.query(Asset).filter(Asset.id == link_id).one()
    skip = AssetSkip(occurred_at=datetime.utcnow())
    asset.skips.append(skip)
    db.session.add(asset)
    db.session.commit()
    return redirect(url_for("main.suggested_link"))


@main.route("/link/<link_id>/read", methods=["POST"])
@login_required
def read_link(link_id):
    asset = db.session.query(Asset).filter(Asset.id == link_id).one()
    asset.read_at = datetime.utcnow()
    return redirect(url_for("main.suggested_link"))


@main.route("/filter/select", methods=["GET", "POST"])
@login_required
def select_filter():
    if request.method == "POST":
        session["tag_filter"] = request.form["tag"]
        return redirect(url_for("main.suggested_link"))
    else:
        tags = [
            r[0]
            for r in db.session.query(AssetTag.tag)
            .join(Asset)
            .filter(Asset.user_id == current_user.id)
            .group_by(AssetTag.tag)
            .all()
        ]
        return render_template("filter_select.html", tags=tags)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/profile", methods=["GET"])
@login_required
def profile_get():
    return render_template("profile.html")


@main.route("/profile", methods=["POST"])
@login_required
def profile_post():
    flash("Profile updated")
    current_user.pinboard_auth = request.form.get("pinboard_auth")
    db.session.add(current_user)
    db.session.commit()
    return render_template("profile.html")


def build_new_asset(link):
    id_ = link["hash"]
    asset = Asset(
        upstream_id=id_,
        url=link["href"],
        title=link["description"],
        change_hash=link["meta"],
        pinboard_created_at=maya.parse(link["time"]).datetime(),
    )
    for tag_str in link["tags"].split():
        tag = AssetTag(tag=tag_str)
        asset.tags.append(tag)
    return asset


def update_tags(asset, link_tags):
    current_tags = set(link_tags.split())
    existing_tags = {t.tag for t in asset.tags}
    remove_tags = [t for t in asset.tags if t.tag in existing_tags - current_tags]
    for tag in remove_tags:
        db.session.delete(tag)
    new_tags = current_tags - existing_tags
    for tag in new_tags:
        asset.tags.append(AssetTag(tag=tag))
