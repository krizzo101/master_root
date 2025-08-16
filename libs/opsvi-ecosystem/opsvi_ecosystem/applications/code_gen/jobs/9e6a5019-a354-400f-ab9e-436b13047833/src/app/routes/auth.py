"""
User authentication routes: registration, login, logout, profile.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import bcrypt, db
from app.forms import LoginForm, RegistrationForm
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.homepage"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data, email=form.email.data, password_hash=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.homepage"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Login successful.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.homepage"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.homepage"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html", user=current_user)
