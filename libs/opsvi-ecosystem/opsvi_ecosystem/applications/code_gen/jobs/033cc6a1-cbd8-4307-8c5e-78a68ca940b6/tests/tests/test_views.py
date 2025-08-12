import pytest
from app import create_app
from unittest.mock import patch, MagicMock

@pytest.fixture
    def client():
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client



@patch('app.views.get_weather_client')
@patch('app.views.render_template')
def test_index_page_renders_with_weather_data(mock_render, mock_client_factory, client):
    # Setup mock WeatherClient
    mock_client = MagicMock()
    mock_client.get_weather.return_value = {'weather': [{'description': 'sunny'}], 'main': {'temp': 25}, 'name': 'TestCity'}
    mock_client_factory.return_value = mock_client

    response = client.get('/')
    # Assert route returns HTTP 200
    assert response.status_code == 200
    # Assert render_template called with template and weather data
    mock_render.assert_called_once()
    args, kwargs = mock_render.call_args
    assert 'weather' in kwargs or (len(args) > 0 and isinstance(args[1], dict))
    assert response.content_type == 'text/html; charset=utf-8'


@patch('app.views.get_weather_client')
@patch('app.views.render_template')
from app.weather_client import WeatherAPIError

def test_index_page_handles_weather_api_error_and_displays_message(mock_render, mock_client_factory, client):
    mock_client = MagicMock()
    mock_client.get_weather.side_effect = WeatherAPIError("API failure")
    mock_client_factory.return_value = mock_client

    response = client.get('/')
    assert response.status_code == 200
    mock_render.assert_called_once()
    args, kwargs = mock_render.call_args
    # The render should include an error message in the context
    assert 'error' in kwargs or 'message' in kwargs

