from flask import Flask, render_template
import httpx
import os
import random


def create_app():
    app = Flask(__name__)
    app.config["PINBOARD_AUTH_TOKEN"] = os.environ.get("PINBOARD_AUTH_TOKEN")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    return app


app = create_app()


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/link/suggested")
def suggested_link():
    pinboard_auth = app.config["PINBOARD_AUTH_TOKEN"]
    links = httpx.get(
        f"https://api.pinboard.in/v1/posts/all?auth_token={pinboard_auth}&format=json"
    ).json()
    pinboard_href = random.choice(links)["href"]
    return render_template("suggested_link.html", pinboard_href=pinboard_href)
