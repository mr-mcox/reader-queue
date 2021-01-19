from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import os
import logging

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command("db", MigrateCommand)


@manager.command
def backfill_biblios():
    from readerqueue.models import Asset
    from readerqueue.main import update_biblio, download_html_serial
    import nltk

    nltk.download("punkt")

    assets = db.session.query(Asset).all()
    asset_htmls = download_html_serial(assets=assets)
    for asset, html in asset_htmls:
        update_biblio(asset, html=html)

    for asset in assets:
        db.session.add(asset)
    db.session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager.run()
