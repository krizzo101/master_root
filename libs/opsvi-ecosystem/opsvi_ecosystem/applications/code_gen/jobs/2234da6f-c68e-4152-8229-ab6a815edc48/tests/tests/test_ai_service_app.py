import pytest
from ai_service.app import SummarizeRequest, SummarizeResponse, SuggestRequest, SuggestResponse

@pytest.fixture
 def sample_summarize_request():
     return SummarizeRequest(document_text="This is a sample document text for summarization.")

@pytest.fixture
 def sample_suggest_request():
     return SuggestRequest(document_text="This is a sample document text for suggestion.")


def test_summarize_request_initialization_with_valid_text(sample_summarize_request):
    assert isinstance(sample_summarize_request, SummarizeRequest)
    assert sample_summarize_request.document_text == "This is a sample document text for summarization."


def test_summarize_request_empty_document_text_raises_value_error():
    with pytest.raises(ValueError):
        SummarizeRequest(document_text="")


def test_summarize_response_creation_and_content_validation():
    summary = "This document is a sample for testing summarization."
    response = SummarizeResponse(summarized_text=summary)
    assert isinstance(response, SummarizeResponse)
    assert response.summarized_text == summary
    assert len(response.summarized_text) > 0


def test_suggest_request_initialization_and_document_text_assignment(sample_suggest_request):
    assert isinstance(sample_suggest_request, SuggestRequest)
    assert sample_suggest_request.document_text == "This is a sample document text for suggestion."


def test_suggest_request_with_None_document_text_raises_type_error():
    with pytest.raises(TypeError):
        SuggestRequest(document_text=None)


def test_suggest_response_creation_and_suggestions_content():
    suggestions = ["Add more details in introduction.", "Use simpler language."]
    response = SuggestResponse(suggestions=suggestions)
    assert isinstance(response, SuggestResponse)
    assert isinstance(response.suggestions, list)
    assert all(isinstance(s, str) for s in response.suggestions)
    assert len(response.suggestions) == 2


def test_summarize_response_with_empty_summary_string():
    response = SummarizeResponse(summarized_text="")
    assert isinstance(response, SummarizeResponse)
    assert response.summarized_text == ""


def test_suggest_response_with_empty_suggestions_list():
    response = SuggestResponse(suggestions=[])
    assert isinstance(response, SuggestResponse)
    assert response.suggestions == []

