from flask import Flask
from readerqueue.models import Asset, AssetSkip, AssetTag
import os
from flask_sqlalchemy import SQLAlchemy
import logging
from flask_bootstrap import Bootstrap
from flask_login import LoginManager


db = SQLAlchemy()


def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["PINBOARD_AUTH_TOKEN"] = os.environ.get("PINBOARD_AUTH_TOKEN")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ADMIN_USER"] = os.environ.get("ADMIN_USER")
    app.logger.setLevel(logging.INFO)
    login_manager = LoginManager()
    login_manager.login_view = "auth.login_get"
    login_manager.init_app(app)
    db.init_app(app)
    Bootstrap(app)
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).filter(User.id == user_id).first()

    return app
