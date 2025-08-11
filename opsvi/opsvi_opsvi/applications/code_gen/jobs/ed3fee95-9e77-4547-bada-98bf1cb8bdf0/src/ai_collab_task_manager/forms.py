from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    PasswordField,
    BooleanField,
    DateTimeField,
    IntegerField,
    SelectField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from .models import Team, User


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Register")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already registered.")


class TaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField("Description", validators=[Length(max=1024)])
    due_date = DateTimeField(
        "Due Date", validators=[DataRequired()], format="%Y-%m-%dT%H:%M"
    )
    team = SelectField("Team", coerce=int)
    submit = SubmitField("Save Task")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team.choices = [(t.id, t.name) for t in Team.query.all()]


class CommentForm(FlaskForm):
    content = TextAreaField(
        "Comment", validators=[DataRequired(), Length(min=1, max=1000)]
    )
    submit = SubmitField("Add Comment")
