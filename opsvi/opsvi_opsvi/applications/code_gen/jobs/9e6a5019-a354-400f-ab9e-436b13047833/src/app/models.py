"""
SQLAlchemy models for CMS core entities: User, Post, Category, Tag, Image, PostView.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from . import db

# Association tables for many-to-many relationships
post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)

post_categories = db.Table(
    "post_categories",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column(
        "category_id", db.Integer, db.ForeignKey("category.id"), primary_key=True
    ),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship("Post", backref="author", lazy=True)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    seo_summary = db.Column(db.String(512), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    images = db.relationship(
        "Image", backref="post", lazy=True, cascade="all,delete-orphan"
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    views = db.relationship(
        "PostView", backref="post", lazy=True, cascade="all,delete-orphan"
    )
    tags = db.relationship(
        "Tag", secondary=post_tags, backref=db.backref("posts", lazy="dynamic")
    )
    categories = db.relationship(
        "Category",
        secondary=post_categories,
        backref=db.backref("posts", lazy="dynamic"),
    )

    def view_count(self) -> int:
        return len(self.views)

    def __repr__(self) -> str:
        return f"<Post {self.title}>"


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    alt_text = db.Column(db.String(256), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    url = db.Column(db.String(512), nullable=True)

    def __repr__(self) -> str:
        return f"<Image {self.filename}>"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=True)

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class PostView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("views", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<PostView post_id={self.post_id} user_id={self.user_id}>"
