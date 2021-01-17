from flask import request, flash, url_for, current_app, render_template, Blueprint
from flask_login import login_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect

from readerqueue import db
from readerqueue.models import User


auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=["POST"])
def signup_post():
    email = request.form.get("email")
    password = request.form.get("password")

    user = db.session.query(User).filter_by(email=email).first()

    if user:
        flash("Email address already exists")
        return redirect(url_for("auth.signup_get"))

    if email != current_app.config["ADMIN_USER"]:
        flash("Only one user allowed at this time")
        return redirect(url_for("auth.signup_get"))

    new_user = User(
        email=email, password_hash=generate_password_hash(password, method="sha256")
    )

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for("auth.login"))


@auth.route("/signup", methods=["GET"])
def signup_get():
    return render_template("signup.html")


@auth.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")

    user = db.session.query(User).filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        flash("Please check your login details and try again.")
        return redirect(url_for("auth.login_get"))
    login_user(user, remember=True)

    return redirect(url_for("main.index"))
