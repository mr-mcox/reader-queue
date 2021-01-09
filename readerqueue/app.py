from flask import Flask, render_template
from readerqueue.models import Asset, AssetSkip
import httpx
import os
import random
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime
from sqlalchemy import func


app = Flask(__name__)
app.config["PINBOARD_AUTH_TOKEN"] = os.environ.get("PINBOARD_AUTH_TOKEN")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/link/suggested")
def suggested_link():
    pinboard_auth = app.config["PINBOARD_AUTH_TOKEN"]
    links = httpx.get(
        f"https://api.pinboard.in/v1/posts/all?auth_token={pinboard_auth}&format=json"
    ).json()
    for link in links:
        id_ = hashlib.sha3_256(link["href"].encode("utf-8")).hexdigest()
        asset = db.session.query(Asset).filter(Asset.id == id_).one_or_none()
        if asset is None:
            asset = Asset(id=id_, url=link["href"])
            db.session.add(asset)
    db.session.commit()
    assets = (
        db.session.query(Asset)
        .outerjoin(AssetSkip)
        .group_by(Asset.id)
        .having(func.count(1) < 3)
        .all()
    )
    url = random.choice(assets).url
    return render_template("suggested_link.html", pinboard_href=url)


@app.route("/link/<link_id>/skip", methods=["POST"])
def skip_link(link_id):
    asset = db.session.query(Asset).filter(Asset.id == link_id).one()
    skip = AssetSkip(occurred_at=datetime.utcnow())
    asset.skips.append(skip)
    db.session.add(asset)
    db.session.commit()
    return ""
