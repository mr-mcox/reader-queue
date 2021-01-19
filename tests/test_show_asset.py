import pytest
from readerqueue.models import Base, Asset
from sqlalchemy import create_engine
from flask import url_for

from readerqueue import create_app

import os


@pytest.fixture
def app():

    app = create_app()
    db_pass = os.environ.get("DB_PASS")

    db_uri = f"postgresql://readerqueue:{db_pass}@localhost:5432/reader-queue-test"
    engine = create_engine(db_uri)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "NOtSecret"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["ADMIN_USER"] = "me@me.com"
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield app
    Base.metadata.drop_all(engine)


def test_show_link(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.pinboard.in/v1/posts/all?auth_token=pb_auth:pb_token&format=json&meta=1",
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
    httpx_mock.add_response(data=sample_html)
    signup_and_login(client)
    client.get("/link/sync")
    rv = client.get("/link/suggested")
    assert "https://fs.blog/2018/12/habits-james-clear/" in rv.data.decode("utf-8")
    assert "Why Small Habits Make a Big Difference" in rv.data.decode("utf-8")


def test_do_not_show_after_three_skips(httpx_mock, client):
    from readerqueue.main import db

    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pb_auth:pb_token&format=json&meta=1",
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
    httpx_mock.add_response(data=sample_html)
    signup_and_login(client)
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
        client.post(url_for("main.skip_link", link_id=skip_asset.id, _external=False))

    for _ in range(10):
        rv = client.get("/link/suggested")
        assert skip_url not in rv.data.decode("utf-8")


def test_do_not_show_if_read(httpx_mock, client):
    from readerqueue.main import db

    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pb_auth:pb_token&format=json&meta=1",
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
    httpx_mock.add_response(data=sample_html)
    signup_and_login(client)
    client.get("/link/sync")
    read_url = "https://huggingface.co/blog/ray-tune"
    read_url_seen = False
    for i in range(10):
        rv = client.get("/link/suggested")
        if read_url in rv.data.decode("utf-8"):
            read_url_seen = True
            break
    assert read_url_seen

    read_asset = db.session.query(Asset).filter(Asset.url == read_url).one()
    client.post(url_for("main.read_link", link_id=read_asset.id, _external=False))

    for _ in range(10):
        rv = client.get("/link/suggested")
        assert read_url not in rv.data.decode("utf-8")


def test_show_tags(httpx_mock, client):
    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pb_auth:pb_token&format=json&meta=1",
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
                "tags": "habits productivity",
            },
        ],
    )
    httpx_mock.add_response(data=sample_html)
    signup_and_login(client)
    client.get("/link/sync")
    rv = client.get("/filter/select")
    assert "habits" in rv.data.decode("utf-8")
    assert "productivity" in rv.data.decode("utf-8")


def test_update_tags(httpx_mock, client):
    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pb_auth:pb_token&format=json&meta=1",
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
                "tags": "habits james",
            },
        ],
    )
    httpx_mock.add_response(data=sample_html)
    signup_and_login(client)
    client.get("/link/sync")
    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pb_auth:pb_token&format=json&meta=1",
        json=[
            {
                "href": "https://fs.blog/2018/12/habits-james-clear/",
                "description": "Why Small Habits Make a Big Difference",
                "extended": "",
                "meta": "new_meta",
                "hash": "a9b262277a603c023b9fd20d613a9193",
                "time": "2020-11-15T20:04:09Z",
                "shared": "no",
                "toread": "yes",
                "tags": "habits productivity",
            },
        ],
    )
    client.get("/link/sync")
    rv = client.get("/filter/select")
    assert "habits" in rv.data.decode("utf-8")
    assert "james" not in rv.data.decode("utf-8")
    assert "productivity" in rv.data.decode("utf-8")


def test_filter_by_selected(httpx_mock, client):
    httpx_mock.add_response(
        "https://api.pinboard.in/v1/posts/all?auth_token=pb_auth:pb_token&format=json&meta=1",
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
                "tags": "productivity",
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
                "tags": "machine-learning",
            },
        ],
    )
    httpx_mock.add_response(data=sample_html)
    signup_and_login(client)
    expected_url = 'https://fs.blog/2018/12/habits-james-clear/"'
    client.get("/link/sync")
    client.post("/filter/select", data={"tag": "productivity"})
    for _ in range(10):
        rv = client.get("/link/suggested")
        assert expected_url in rv.data.decode("utf-8")


def signup_and_login(client):
    client.post("/signup", data={"email": "me@me.com", "password": "123"})
    client.post("/login", data={"email": "me@me.com", "password": "123"})
    client.post("/profile", data={"pinboard_auth": "pb_auth:pb_token"})


sample_html = """
<!doctype html>
<html lang="en">
<head>
    
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.3.1/dist/css/bootstrap.min.css" type="text/css">
    

    <title>Why Small Habits Make a Big Difference</title>
    
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent"
            aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav mr-auto">
            
    <li class="nav-item">
    <a class=" nav-link "
       href="/">
        Home 
    </a>
    </li>

        </ul>
        <ul class="navbar-nav mr-auto">
            
    <li class="nav-item">
    <a class=" nav-link "
       href="/filter/select">
        Filter 
    </a>
    </li>

        </ul>
        <ul class="navbar-nav mr-auto">
            
    <li class="nav-item">
    <a class=" nav-link "
       href="/logout">
        Logout 
    </a>
    </li>

        </ul>
    </div>
</nav>

<!-- Your page content -->

<div class="container">
    <div class="row">
        <a href="https://www.askalana.com/the-big-rocks-and-the-jar-a-lesson-in-making-priorities/" target="_blank" rel="noopener noreferrer">The Big Rocks and the Jar: A Lesson in Making Priorities - askAlana.com</a>
    </div>
    <div class="row">
        <div class="col-sm">
            <form method="POST" action="/link/189e9630-2e6a-45db-8926-c7f56f56c70c/skip">
                <input type="submit" class="btn btn-primary" value="Skip">
            </form>
        </div>
        <div class="col-sm">
            <form method="POST" action="/link/189e9630-2e6a-45db-8926-c7f56f56c70c/read">
                <input type="submit" class="btn btn-secondary" value="Complete">
            </form>
        </div>
        <div class="col-sm">

            <a class="btn btn-success" href="https://www.askalana.com/the-big-rocks-and-the-jar-a-lesson-in-making-priorities/" target="_blank" rel="noopener noreferrer" role="button">Read</a>
        </div>
    </div>
</div>
</div>




<!-- Optional JavaScript -->
<script src="https://cdn.jsdelivr.net/npm/jquery@3.4.1/dist/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.14.0/dist/umd/popper.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.3.1/dist/js/bootstrap.min.js"></script>

</body>
</html>
"""
