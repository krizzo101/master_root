import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_base_html_render_template(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert "<title>" in html
    assert "Weather" in html or "weather" in html.lower()


def test_404_html_template_rendered_on_404_error(client):
    response = client.get("/nonexistentpage")
    assert response.status_code == 404
    html = response.get_data(as_text=True)
    assert "404" in html or "not found" in html.lower()


def test_500_error_page_rendering(client):
    # To test 500 error page, we can trigger error inside route temporarily
    @client.application.route("/trigger500")
    def trigger_500():
        raise Exception("Intentional")

    response = client.get("/trigger500")
    assert response.status_code == 500
    html = response.get_data(as_text=True)
    assert "500" in html or "server error" in html.lower()
