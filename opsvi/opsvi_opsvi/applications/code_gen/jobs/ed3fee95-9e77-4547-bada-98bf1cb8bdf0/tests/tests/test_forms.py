import pytest
from ai_collab_task_manager.forms import RegisterForm, LoginForm, TaskForm, CommentForm


from wtforms import Form, StringField
from wtforms.validators import DataRequired


class DummyRegisterForm(RegisterForm):
    email = StringField("Email", validators=[DataRequired()])


def test_registerform_email_validation_accepts_valid_email():
    form = DummyRegisterForm(email="valid@example.com")
    # Form should validate normally with correct email format
    form.email.data = "valid@example.com"
    form.validate_email(form.email)
    assert True  # If no exception, passes


def test_registerform_email_validation_rejects_invalid_email():
    from wtforms.validators import ValidationError

    form = RegisterForm(email="notanemail")
    form.email.data = "invalid-email"

    with pytest.raises(ValidationError):
        form.validate_email(form.email)


def test_taskform_init_assigns_fields():
    data = {"title": "Test Task", "description": "Desc"}
    form = TaskForm(data=data)
    assert form.title.data == data["title"]
    assert form.description.data == data["description"]
