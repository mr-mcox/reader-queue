from flask import Flask
from readerqueue.models import Asset, AssetSkip, AssetTag
import os
from flask_sqlalchemy import SQLAlchemy
import logging
from flask_bootstrap import Bootstrap


db = SQLAlchemy()


def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["PINBOARD_AUTH_TOKEN"] = os.environ.get("PINBOARD_AUTH_TOKEN")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.logger.setLevel(logging.INFO)
    db.init_app(app)
    Bootstrap(app)
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)
    return app
