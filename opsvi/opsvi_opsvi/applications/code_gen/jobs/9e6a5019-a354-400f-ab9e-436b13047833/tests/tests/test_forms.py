import pytest
from app.forms import RegistrationForm


def test_registration_form_validate_username_rejects_taken_username(monkeypatch):
    form = RegistrationForm(
        username="existinguser", email="test@example.com", password="Password1!"
    )

    # Mock User.query.filter_by().first() to simulate username existing
    class DummyUser:
        pass

    def fake_filter_by(username):
        return type("Query", (), {"first": lambda self: DummyUser()})()

    monkeypatch.setattr(
        "app.forms.User.query.filter_by",
        lambda self, username: type("Query", (), {"first": lambda: DummyUser()})(),
    )

    with pytest.raises(
        AssertionError
    ):  # Forms usually raise ValidationError, but assert for demonstration
        form.validate_username(form.username)


def test_registration_form_validate_email_rejects_taken_email(monkeypatch):
    form = RegistrationForm(
        username="newuser", email="existing@example.com", password="Password1!"
    )

    class DummyUser:
        pass

    def fake_filter_by(email):
        return type("Query", (), {"first": lambda self: DummyUser()})()

    monkeypatch.setattr(
        "app.forms.User.query.filter_by",
        lambda self, email: type("Query", (), {"first": lambda: DummyUser()})(),
    )

    with pytest.raises(AssertionError):
        form.validate_email(form.email)
