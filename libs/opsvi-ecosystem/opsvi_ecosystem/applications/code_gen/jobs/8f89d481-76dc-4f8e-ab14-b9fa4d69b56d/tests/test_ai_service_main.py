from unittest.mock import patch

import pytest
from ai_service.main import (
    SuggestionRequest,
    SuggestionResponse,
    SummarizeRequest,
    SummarizeResponse,
    get_suggestion_generator,
    get_summarizer,
    health_check,
    suggest,
    summarize,
    verify_jwt,
)


@pytest.fixture
def valid_jwt_credentials():
    return {"token": "valid.jwt.token"}


@pytest.fixture
def invalid_jwt_credentials():
    return {"token": "invalid.jwt.token"}


@pytest.fixture
def mock_user():
    return {"id": "user123", "roles": ["editor"]}


@pytest.fixture
def summarize_request_data():
    return SummarizeRequest(document_text="Hello world. This is a test document.")


@pytest.fixture
def suggestion_request_data():
    return SuggestionRequest(document_text="This document needs improvement in style.")


@pytest.fixture
def mock_summarizer():
    class MockSummarizer:
        def summarize(self, text):
            return "Summary text."

    return MockSummarizer()


@pytest.fixture
def mock_suggestion_generator():
    class MockSuggestionGenerator:
        def suggest(self, text):
            return ["Suggestion 1", "Suggestion 2"]

    return MockSuggestionGenerator()


def test_get_summarizer_returns_callable_object():
    summarizer = get_summarizer()
    assert hasattr(
        summarizer, "summarize"
    ), "Summarizer object must have 'summarize' method"
    result = summarizer.summarize("Some document text.")
    assert isinstance(result, str), "Summarize method must return a string"


def test_get_suggestion_generator_returns_callable_object():
    suggestion_generator = get_suggestion_generator()
    assert hasattr(
        suggestion_generator, "suggest"
    ), "Suggestion generator must have 'suggest' method"
    result = suggestion_generator.suggest("Some document text.")
    assert isinstance(result, list), "Suggest method must return a list"
    assert all(isinstance(s, str) for s in result), "All suggestions must be strings"


def test_verify_jwt_valid_token_returns_true(valid_jwt_credentials):
    with patch("ai_service.main.verify_jwt") as jwt_mock:
        jwt_mock.return_value = True
        assert verify_jwt(valid_jwt_credentials) is True


def test_verify_jwt_invalid_token_returns_false(invalid_jwt_credentials):
    with patch("ai_service.main.verify_jwt") as jwt_mock:
        jwt_mock.return_value = False
        assert verify_jwt(invalid_jwt_credentials) is False


def test_health_check_returns_healthy_status():
    response = health_check()
    assert isinstance(response, dict), "health_check must return dict"
    assert "status" in response, "Response must contain status key"
    assert response["status"] == "healthy", "Status should be healthy"


@patch("ai_service.main.get_summarizer")
@patch("ai_service.main.verify_jwt", return_value=True)
def test_summarize_successful_returns_response(
    mock_verify_jwt,
    mock_get_summarizer,
    summarize_request_data,
    mock_user,
    mock_summarizer,
):
    mock_get_summarizer.return_value = mock_summarizer
    response = summarize(summarize_request_data, mock_user)
    assert isinstance(response, SummarizeResponse), "Response must be SummarizeResponse"
    assert hasattr(response, "summary"), "Response must have summary attribute"
    assert (
        response.summary == "Summary text."
    ), "Summary content must match mocked output"
    mock_verify_jwt.assert_not_called()  # Assuming JWT verification is outside summarize


def test_summarize_with_empty_document_text_returns_error(mock_user):
    empty_req = SummarizeRequest(document_text="")
    with pytest.raises(ValueError):
        summarize(empty_req, mock_user)


@patch("ai_service.main.get_suggestion_generator")
@patch("ai_service.main.verify_jwt", return_value=True)
def test_suggest_successful_returns_suggestions(
    mock_verify_jwt,
    mock_get_suggestion_generator,
    suggestion_request_data,
    mock_user,
    mock_suggestion_generator,
):
    mock_get_suggestion_generator.return_value = mock_suggestion_generator
    response = suggest(suggestion_request_data, mock_user)
    assert isinstance(
        response, SuggestionResponse
    ), "Response must be SuggestionResponse"
    assert hasattr(response, "suggestions"), "Response must have suggestions attribute"
    assert isinstance(response.suggestions, list), "Suggestions must be a list"
    assert "Suggestion 1" in response.suggestions, "Mock suggestion missing in response"
    mock_verify_jwt.assert_not_called()


def test_suggest_with_non_text_document_raises_error(mock_user):
    bad_req = SuggestionRequest(document_text=None)
    with pytest.raises(TypeError):
        suggest(bad_req, mock_user)

    empty_req = SuggestionRequest(document_text="")
    with pytest.raises(ValueError):
        suggest(empty_req, mock_user)


def test_summarize_request_data_structure_correctness():
    req = SummarizeRequest(document_text="Example text")
    assert hasattr(req, "document_text"), "SummarizeRequest must contain document_text"
    assert req.document_text == "Example text"


def test_summarize_response_data_structure_correctness():
    resp = SummarizeResponse(summary="This is summary.")
    assert hasattr(resp, "summary"), "SummarizeResponse must contain summary"
    assert resp.summary == "This is summary."


def test_suggestion_request_data_structure_correctness():
    req = SuggestionRequest(document_text="Example doc")
    assert hasattr(req, "document_text"), "SuggestionRequest must contain document_text"
    assert req.document_text == "Example doc"


def test_suggestion_response_data_structure_correctness():
    resp = SuggestionResponse(suggestions=["Suggestion 1", "Suggestion 2"])
    assert hasattr(resp, "suggestions"), "SuggestionResponse must contain suggestions"
    assert isinstance(resp.suggestions, list), "suggestions must be a list"
    assert "Suggestion 1" in resp.suggestions


def test_summarize_handles_large_input(mock_user):
    large_text = "word " * 10000  # Large input
    req = SummarizeRequest(document_text=large_text)
    response = summarize(req, mock_user)
    assert isinstance(response, SummarizeResponse)
    assert isinstance(response.summary, str)
    assert len(response.summary) < len(
        large_text
    ), "Summary should be smaller than input"


def test_suggest_handles_large_input(mock_user):
    large_text = "word " * 10000
    req = SuggestionRequest(document_text=large_text)
    response = suggest(req, mock_user)
    assert isinstance(response, SuggestionResponse)
    assert isinstance(response.suggestions, list)
    assert len(response.suggestions) > 0, "Suggestions should not be empty"


def test_verify_jwt_raises_exception_on_malformed_credentials():
    malformed_credentials = {}
    with pytest.raises(KeyError):
        verify_jwt(malformed_credentials)

    malformed_credentials = {"token": None}
    result = verify_jwt(malformed_credentials)
    assert result is False or result is None
