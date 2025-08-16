"""
Configure Flask-Admin views for all models.
"""
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from .models import Category, Image, Post, Tag, User


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for

        return redirect(url_for("auth.login"))


def register_admin_views(admin, db):
    admin.add_view(SecureModelView(User, db.session))
    admin.add_view(SecureModelView(Post, db.session))
    admin.add_view(SecureModelView(Image, db.session))
    admin.add_view(SecureModelView(Category, db.session))
    admin.add_view(SecureModelView(Tag, db.session))
