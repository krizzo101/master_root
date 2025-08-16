"""
WTForms forms: User Registration, Login, Post Editor, Image Upload, Category, Tag.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    TextAreaField,
    SubmitField,
    SelectMultipleField,
    FileField,
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
from .models import User


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 128)])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username: StringField) -> None:
        from .models import User

        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, email: StringField) -> None:
        from .models import User

        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(3, 200)])
    content = TextAreaField("Content", validators=[DataRequired()])
    categories = SelectMultipleField("Categories", coerce=int)
    tags = SelectMultipleField("Tags", coerce=int)
    submit = SubmitField("Save")
    ai_generate = SubmitField("Generate using AI")


class ImageUploadForm(FlaskForm):
    image = FileField(
        "Image", validators=[FileRequired(), FileAllowed(["jpg", "jpeg", "png", "gif"])]
    )
    submit = SubmitField("Upload")


class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(1, 80)])
    description = StringField("Description", validators=[Length(max=256)])
    submit = SubmitField("Save")


class TagForm(FlaskForm):
    name = StringField("Tag Name", validators=[DataRequired(), Length(1, 80)])
    submit = SubmitField("Save")
