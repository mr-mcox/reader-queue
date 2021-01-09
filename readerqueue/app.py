from flask import Flask, render_template, redirect, url_for
from readerqueue.models import Asset, AssetSkip
import httpx
import os
import random
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime
from sqlalchemy import func
import maya
import math


app = Flask(__name__)
app.config["PINBOARD_AUTH_TOKEN"] = os.environ.get("PINBOARD_AUTH_TOKEN")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/link/sync")
def sync():
    pinboard_auth = app.config["PINBOARD_AUTH_TOKEN"]
    links = httpx.get(
        f"https://api.pinboard.in/v1/posts/all?auth_token={pinboard_auth}&format=json"
    ).json()
    for link in links:
        id_ = hashlib.sha3_256(link["href"].encode("utf-8")).hexdigest()
        asset = db.session.query(Asset).filter(Asset.id == id_).one_or_none()
        if asset is None:
            asset = Asset(id=id_, url=link["href"], pinboard_created_at=maya.parse(link["time"]).datetime())
            db.session.add(asset)
    db.session.commit()
    return redirect(url_for("suggested_link"))


@app.route("/link/suggested")
def suggested_link():
    result = (
        db.session.query(Asset, Asset.pinboard_created_at, func.count(AssetSkip.id))
        .outerjoin(AssetSkip)
        .group_by(Asset.id)
        .having(func.count(1) < 3)
        .all()
    )
    assets, created_at, skips = list(zip(*result))
    days_passed_ln = [math.log((datetime.now() - d).days) for d in created_at]
    days_passed_adj = [d + s for d, s in zip(days_passed_ln, skips)]
    if len(days_passed_adj) > 1:
        max_score = max(*days_passed_adj) + 0.1
    else:
        max_score = days_passed_adj[0] + 0.1
    weights = [max_score - x for x in days_passed_adj]
    url = random.choices(assets, k=1, weights=weights )[0].url
    return render_template("suggested_link.html", pinboard_href=url)


@app.route("/link/<link_id>/skip", methods=["POST"])
def skip_link(link_id):
    asset = db.session.query(Asset).filter(Asset.id == link_id).one()
    skip = AssetSkip(occurred_at=datetime.utcnow())
    asset.skips.append(skip)
    db.session.add(asset)
    db.session.commit()
    return redirect(url_for("suggested_link"))
