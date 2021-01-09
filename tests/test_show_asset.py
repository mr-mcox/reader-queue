import pytest
from readerqueue.models import Base, Asset
from sqlalchemy import create_engine
from flask import url_for

import os


@pytest.fixture
def app():
    from readerqueue.app import app

    db_pass = os.environ.get("DB_PASS")

    db_uri = f"postgresql://readerqueue:{db_pass}@localhost:5432/reader-queue-test"
    engine = create_engine(db_uri)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["PINBOARD_AUTH_TOKEN"] = "pinboard:auth"
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield app
    Base.metadata.drop_all(engine)


def test_show_link(httpx_mock, client):
    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pinboard:auth&format=json",
        json=[
            {
                "href": "https://fs.blog/2018/12/habits-james-clear/",
                "description": "Why Small Habits Make a Big Difference",
                "extended": "",
                "meta": "58d345907a0d7379d0084efe0523e7e9",
                "hash": "a9b262277a603c023b9fd20d613a9193",
                "time": "2021-01-04T16:32:40Z",
                "shared": "no",
                "toread": "yes",
                "tags": "",
            }
        ],
    )
    client.get("/link/sync")
    rv = client.get("/link/suggested")
    assert "https://fs.blog/2018/12/habits-james-clear/" in rv.data.decode("utf-8")


def test_do_not_show_after_three_skips(httpx_mock, client):
    from readerqueue.app import db, skip_link, app

    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pinboard:auth&format=json",
        json=[
            {
                "href": "https://fs.blog/2018/12/habits-james-clear/",
                "description": "Why Small Habits Make a Big Difference",
                "extended": "",
                "meta": "58d345907a0d7379d0084efe0523e7e9",
                "hash": "a9b262277a603c023b9fd20d613a9193",
                "time": "2020-11-15T20:04:09Z",
                "shared": "no",
                "toread": "yes",
                "tags": "",
            },
            {
                "href": "https://huggingface.co/blog/ray-tune",
                "description": "Hyperparameter Search with Transformers and Ray Tune",
                "extended": "",
                "meta": "f62faab7d5e6f28c8a3cf1ff771632cd",
                "hash": "75270ca9c0996db589b4abb733cadd05",
                "time": "2021-01-04T16:32:40Z",
                "shared": "no",
                "toread": "yes",
                "tags": "",
            },
        ],
    )
    client.get("/link/sync")
    skip_url = "https://huggingface.co/blog/ray-tune"
    skip_url_seen = False
    for i in range(10):
        rv = client.get("/link/suggested")
        if skip_url in rv.data.decode("utf-8"):
            skip_url_seen = True
            break
    assert skip_url_seen

    skip_asset = db.session.query(Asset).filter(Asset.url == skip_url).one()
    # Post skip three times
    for _ in range(3):
        client.post(url_for("skip_link", link_id=skip_asset.id, _external=False))

    for _ in range(10):
        rv = client.get("/link/suggested")
        assert skip_url not in rv.data.decode("utf-8")
