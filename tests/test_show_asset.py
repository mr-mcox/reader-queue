import pytest
from readerqueue.models import Base
from sqlalchemy import create_engine
import os


@pytest.fixture
def client():
    from readerqueue.app import app

    db_pass = os.environ.get("DB_PASS")

    db_uri = f"postgresql://readerqueue:{db_pass}@localhost:5432/reader-queue-test"
    engine = create_engine(db_uri)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["PINBOARD_AUTH_TOKEN"] = "pinboard:auth"
    client = app.test_client()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with app.app_context():
        yield client
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
    rv = client.get("/link/suggested")
    assert "https://fs.blog/2018/12/habits-james-clear/" in rv.data.decode("utf-8")
