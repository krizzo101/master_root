import pytest
from fastapi.testclient import TestClient
from ai_service.app import app, load_models, summarize, suggest, health_check
from ai_service.app import SummarizeRequest, SummarizeResponse, SuggestionRequest, SuggestionResponse
from unittest.mock import patch, MagicMock

@pytest.fixture(scope='module')
    def client():
        """Create a TestClient for the FastAPI app to test API endpoints."""
        with TestClient(app) as c:
            yield c

@pytest.fixture(scope='function')
    def sample_text():
        return "This is a sample document text for testing summarization and suggestions."


def test_load_models_initialization_success():
    # Assuming load_models returns True when models load successfully
    result = load_models()
    assert result is True, "load_models should return True on successful initialization"

@patch('ai_service.app.load_models')
def test_load_models_failure_handling(mock_load):
    mock_load.side_effect = Exception("Model load failure")
    with pytest.raises(Exception) as excinfo:
        load_models()
    assert "Model load failure" in str(excinfo.value)

def test_summarize_endpoint_success(client, sample_text):
    request_payload = {"text": sample_text}
    response = client.post('/summarize', json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert 'summary' in data
    assert isinstance(data['summary'], str)
    assert len(data['summary']) > 0

def test_summarize_endpoint_invalid_request(client):
    response = client.post('/summarize', json={})
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert 'detail' in data
    # Validate that error message relates to missing required field
    assert any('text' in err['loc'] for err in data['detail'])

def test_summarize_function_invalid_input_type():
    with pytest.raises(AttributeError):  # Assuming function expects request object with attribute 'text'
        summarize(request=None)

def test_summarize_response_model_fields():
    summary_text = "This is a summary."
    response = SummarizeResponse(summary=summary_text)
    assert response.summary == summary_text
    # Test serialization
    serialized = response.json()
    assert 'summary' in serialized

import pydantic

def test_summarize_request_model_validation():
    # Valid input
    req = SummarizeRequest(text="A valid text.")
    assert req.text == "A valid text."

    # Empty string should raise validation error
    with pytest.raises(pydantic.ValidationError):
        SummarizeRequest(text="")

    # Non-string input
    with pytest.raises(pydantic.ValidationError):
        SummarizeRequest(text=123)

def test_suggest_endpoint_success(client, sample_text):
    request_payload = {"text": sample_text}
    response = client.post('/suggest', json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert 'suggestions' in data
    assert isinstance(data['suggestions'], list)
    assert all(isinstance(s, str) for s in data['suggestions'])

def test_suggest_endpoint_invalid_request(client):
    response = client.post('/suggest', json={})
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('text' in err['loc'] for err in data['detail'])

def test_suggestion_request_model_validation():
    valid = SuggestionRequest(text="Some text for suggestions.")
    assert valid.text == "Some text for suggestions."

    import pydantic
    with pytest.raises(pydantic.ValidationError):
        SuggestionRequest(text=None)

    with pytest.raises(pydantic.ValidationError):
        SuggestionRequest(text=12345)

def test_suggestion_response_model_fields():
    suggestions = ["Add more examples.", "Use simple language."]
    response = SuggestionResponse(suggestions=suggestions)
    assert response.suggestions == suggestions
    serialized = response.json()
    assert 'suggestions' in serialized

def test_health_check_returns_200(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert data['status'] == 'ok'

def test_health_check_endpoint_type_and_format(client):
    response = client.get('/health')
    assert response.headers['Content-Type'] == 'application/json'
    data = response.json()
    assert isinstance(data, dict)
    assert 'status' in data
    assert isinstance(data['status'], str)

import time
from fastapi import Request

class DummyRequest:
    def __init__(self, text):
        self.text = text

def test_summarize_function_performance(sample_text):
    req = DummyRequest(text=sample_text * 50)  # Large text
    start = time.perf_counter()
    response = summarize(req)
    end = time.perf_counter()
    elapsed = end - start
    assert isinstance(response, SummarizeResponse)
    assert elapsed <= 1, f"summarize took too long: {elapsed}s"

def test_suggest_function_performance(sample_text):
    class DummyRequest:
        def __init__(self, text):
            self.text = text
    req = DummyRequest(text=sample_text * 50)  # Large text
    import time
    start = time.perf_counter()
    response = suggest(req)
    end = time.perf_counter()
    elapsed = end - start
    assert isinstance(response, SuggestionResponse)
    assert elapsed <= 1, f"suggest took too long: {elapsed}s"

import concurrent.futures

def summarize_single(client, text):
    return client.post('/summarize', json={"text": text})

def test_summarize_endpoint_multiple_clients_simultaneous_requests(client, sample_text):
    texts = [sample_text + f" {i}" for i in range(10)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(summarize_single, client, t) for t in texts]
        results = [f.result() for f in futures]
    for resp in results:
        assert resp.status_code == 200
        data = resp.json()
        assert 'summary' in data
        assert isinstance(data['summary'], str)

def suggest_single(client, text):
    return client.post('/suggest', json={"text": text})

def test_suggest_endpoint_multiple_clients_simultaneous_requests(client, sample_text):
    texts = [sample_text + f" {i}" for i in range(10)]
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(suggest_single, client, t) for t in texts]
        results = [f.result() for f in futures]
    for resp in results:
        assert resp.status_code == 200
        data = resp.json()
        assert 'suggestions' in data
        assert isinstance(data['suggestions'], list)
