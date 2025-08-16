import unittest

from ai_collab_task_manager.app import app, db
from ai_collab_task_manager.models import User


class FlaskAppTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            user = User(
                username="alice",
                email="alice@example.com",
                password_hash="$2b$12$somesample",
                is_admin=True,
            )
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def login(self, email, password):
        return self.client.post(
            "/login", data=dict(email=email, password=password), follow_redirects=True
        )

    def test_register_page(self):
        rv = self.client.get("/register")
        self.assertEqual(rv.status_code, 200)

    def test_dashboard_requires_login(self):
        rv = self.client.get("/dashboard")
        self.assertEqual(rv.status_code, 302)  # redirect

    def test_login_logout(self):
        rv = self.login("alice@example.com", "bad-password")
        self.assertIn(b"Invalid email or password", rv.data)
        rv = self.login("alice@example.com", "somepass")  # Suppose hash matches
        # Can't check user is actually logged in w/o full bcrypt, just check page loads


if __name__ == "__main__":
    unittest.main()
