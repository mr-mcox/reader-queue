from flask import (
    render_template,
    redirect,
    url_for,
    request,
    session,
    Blueprint,
    flash,
)
from flask_login import logout_user, login_required, current_user
from readerqueue.models import Asset, AssetTag, User, AssetEvent
from readerqueue.presenters import AssetPresenter
from sqlalchemy.sql import select, func, functions
import httpx
import random
from datetime import datetime
import maya
import math
from newspaper import Article
import asyncio
from urllib.parse import urlparse
from . import db
import logging


main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
    return render_template("index.html")


@main.route("/link/sync")
@login_required
def sync():
    pinboard_auth = current_user.pinboard_auth
    sync_url = f"https://api.pinboard.in/v1/posts/recent?auth_token={pinboard_auth}&format=json&meta=1"
    client = httpx.Client()
    links = client.get(sync_url).json()
    new_assets = list()
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
            new_assets.append(asset)
            db.session.add(current_user)
        if asset.change_hash != link["meta"]:
            update_tags(asset, link["tags"])
    update_biblio_for_assets(new_assets)
    db.session.commit()
    return redirect(url_for("main.suggested_link"))


@main.route("/link/suggested")
@login_required
def suggested_link():
    engine = db.session.get_bind()
    results = engine.execute(asset_weight_metrics())
    asset_weights = list()
    for r in results:
        score = math.log((datetime.utcnow() - r.bookmarked_at).total_seconds())
        score = score ** 2
        score *= 1.5 ** r.n_skips
        score *= (2 / 3) ** r.n_reads
        asset_weights.append((r.id, 1 / score))
    chosen_weight = random.choices(
        asset_weights, k=1, weights=[a[1] for a in asset_weights]
    )[0]
    return redirect(url_for("main.show_asset", asset_id=chosen_weight[0]))


def asset_weight_metrics():
    asset_table = Asset.__table__
    a_event_table = AssetEvent.__table__
    bookmarked_at_q = (
        select(
            [
                a_event_table.c.asset_id,
                func.min(a_event_table.c.occurred_at).label("bookmarked_at"),
            ]
        )
        .where(a_event_table.c.name == "bookmarked")
        .group_by(a_event_table.c.asset_id)
        .alias("bookmarked_at")
    )
    n_skips_q = (
        select(
            [
                a_event_table.c.asset_id,
                func.count(a_event_table.c.occurred_at).label("n_skips"),
            ]
        )
        .where(a_event_table.c.name == "skipped")
        .group_by(a_event_table.c.asset_id)
        .alias("n_skips")
    )
    n_reads_q = (
        select(
            [
                a_event_table.c.asset_id,
                func.count(a_event_table.c.occurred_at).label("n_read"),
            ]
        )
        .where(a_event_table.c.name == "read")
        .group_by(a_event_table.c.asset_id)
        .alias("n_read")
    )
    query = (
        select(
            [
                asset_table.c.id,
                bookmarked_at_q.c.bookmarked_at,
                functions.coalesce(n_skips_q.c.n_skips, 0).label("n_skips"),
                functions.coalesce(n_reads_q.c.n_read, 0).label("n_reads"),
            ]
        )
        .where(asset_table.c.user_id == current_user.id)
        .where(asset_table.c.status == "active")
    )
    join_tables = [bookmarked_at_q, n_skips_q, n_reads_q]
    tag_filter = session.get("tag_filter")
    if tag_filter is not None and tag_filter != "all":
        tag_table = AssetTag.__table__
        join_tables.append(tag_table)
        query = query.where(tag_table.c.tag == tag_filter)
    joins = asset_table
    for t in join_tables:
        joins = joins.outerjoin(t)
    query = query.select_from(joins)
    return query


@main.route("/link/<link_id>/skip", methods=["POST"])
@login_required
def skip_link(link_id):
    asset = db.session.query(Asset).filter(Asset.id == link_id).one()
    asset.events.append(AssetEvent(name="skipped", occurred_at=datetime.utcnow()))
    db.session.add(asset)
    db.session.commit()
    return redirect(url_for("main.suggested_link"))


@main.route("/asset/<asset_id>", methods=["GET"])
@login_required
def show_asset(asset_id):
    asset = db.session.query(Asset).filter(Asset.id == asset_id).one()
    return render_template("suggested_link.html", asset=AssetPresenter(asset))


@main.route("/asset/last_read", methods=["GET"])
@login_required
def asset_last_read():
    asset = (
        db.session.query(Asset)
        .join(AssetEvent)
        .filter(Asset.user_id == current_user.id)
        .filter(AssetEvent.name == "read")
        .order_by(AssetEvent.occurred_at.desc())
        .first()
    )
    return redirect(url_for("main.show_asset", asset_id=asset.id))


@main.route("/link/<link_id>/read", methods=["POST"])
@login_required
def read_link(link_id):
    asset = db.session.query(Asset).filter(Asset.id == link_id).one()
    asset.events.append(AssetEvent(name="read", occurred_at=datetime.utcnow()))
    db.session.add(asset)
    db.session.commit()
    return redirect(asset.url)


@main.route("/link/<link_id>/archive", methods=["POST"])
@login_required
def archive_link(link_id):
    asset = db.session.query(Asset).filter(Asset.id == link_id).one()
    asset.events.append(AssetEvent(name="archived", occurred_at=datetime.utcnow()))
    asset.status = "archived"
    db.session.add(asset)
    db.session.commit()
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
        description=link["extended"],
        change_hash=link["meta"],
    )
    asset.events.append(
        AssetEvent(name="bookmarked", occurred_at=maya.parse(link["time"]).datetime())
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


def update_biblio(asset, html):
    metadata = dict()
    if len(html) > 0:
        article = Article(url=asset.url)
        article.download(input_html=html)
        article.parse()
        article.nlp()
        to_extract = ["title", "authors", "top_image", "summary", "keywords"]
        for item_name in to_extract:
            item = getattr(article, item_name)
            if len(item) > 0:
                metadata[item_name] = item
        n_words = len(article.text.split())
        if n_words > 0:
            metadata["n_words"] = n_words
    metadata["domain"] = urlparse(asset.url).hostname
    asset.biblio = metadata
    return asset


def asset_html(assets):
    return asyncio.run(download_html_concurrently(assets))


async def download_html_concurrently(assets):
    async with httpx.AsyncClient() as client:
        htmls = await asyncio.gather(*[async_get_html(a.url, client) for a in assets])
    return zip(assets, htmls)


async def async_get_html(url, client):
    try:
        r = await client.get(url)
        logging.info(f"Got {url}")
        return r.text
    except Exception as error:
        logging.warning(f"Failed to get {url} with {type(error)}")
        return ""


def update_biblio_for_assets(new_assets):
    asset_htmls = asset_html(assets=new_assets)
    for asset, html in asset_htmls:
        update_biblio(asset, html=html)


def get_html(url, client):
    try:
        r = client.get(url)
        logging.info(f"Got {url}")
        return r.text
    except Exception as error:
        logging.warning(f"Failed to get {url} with {type(error)}")
        return ""


def download_html_serial(assets):
    client = httpx.Client()
    htmls = [get_html(a.url, client) for a in assets]
    return zip(assets, htmls)
