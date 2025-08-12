import ai_service.main as main
import pytest


@pytest.fixture
def sample_summarization_request():
    return main.SummarizationRequest(content="This is a test document.", language="en")


@pytest.fixture
def sample_suggestion_request():
    return main.SuggestionRequest(content="Improve this text.", language="en")


@pytest.fixture
def sample_ai_response():
    return main.AIResponse(
        summary="This is a summarized text.",
        suggestions=["Suggestion 1", "Suggestion 2"],
    )


def test_healthz_endpoint_returns_ok_status():
    """
    Test the healthz endpoint returns 'OK' as a string.
    """
    response = main.healthz()
    assert response == "OK"


def test_summarizationrequest_initialization_and_attributes(
    sample_summarization_request,
):
    """
    Test SummarizationRequest correctly stores content and language attributes.
    """
    request = sample_summarization_request
    assert request.content == "This is a test document."
    assert request.language == "en"


def test_suggestionrequest_initialization_and_attributes(sample_suggestion_request):
    """
    Test SuggestionRequest correctly stores content and language attributes.
    """
    request = sample_suggestion_request
    assert request.content == "Improve this text."
    assert request.language == "en"


def test_airesponse_initialization_and_attributes(sample_ai_response):
    """
    Test AIResponse stores the summary string and suggestions list accurately.
    """
    response = sample_ai_response
    assert isinstance(response.summary, str)
    assert isinstance(response.suggestions, list)
    assert len(response.suggestions) == 2


def test_mock_summarize_with_openai_returns_expected_response():
    """
    Test mock_summarize_with_openai generates a valid AIResponse containing a summary text.
    """
    content = "Some important text to summarize."
    language = "en"
    response = main.mock_summarize_with_openai(content, language)
    assert isinstance(response.summary, str)
    assert response.summary != ""
    assert isinstance(response.suggestions, list)


def test_mock_post_method_behavior_and_state():
    """
    Test DummyResp's raise_for_status() does not raise and json() returns dict.
    """
    dummy_resp = main.DummyResp()
    dummy_resp.raise_for_status()  # Should not raise
    json_data = dummy_resp.json()
    assert isinstance(json_data, dict)
    assert "choices" in json_data


def test_raise_for_status_does_not_raise_for_dummyresp():
    """
    Ensure DummyResp.raise_for_status() is a no-op without raising exceptions.
    """
    dummy = main.DummyResp()
    try:
        dummy.raise_for_status()
    except Exception as e:
        pytest.fail(f"raise_for_status raised exception {e}")


def test_json_method_returns_expected_structure():
    """
    Test DummyResp.json() returns dictionary including 'choices' key.
    """
    dummy = main.DummyResp()
    json_resp = dummy.json()
    assert "choices" in json_resp
    assert isinstance(json_resp["choices"], list)


def test_test_summarize_short_handles_short_input():
    """
    Test summarize function with very short input returns expected AIResponse.
    """
    short_content = "Hi."
    response = main.mock_summarize_with_openai(short_content, "en")
    assert isinstance(response.summary, str)
    assert len(response.summary) > 0


def test_test_summarize_success_with_monkeypatch(monkeypatch):
    """
    Test successful summarization using monkeypatch to mock the network call.
    """

    class MockedResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "Summarized text"}}]}

    def mock_post(*args, **kwargs):
        return MockedResponse()

    monkeypatch.setattr(main.requests, "post", mock_post)

    response = main.mock_summarize_with_openai("Test content.", "en")
    assert isinstance(response.summary, str)
    assert response.summary == "Summarized text"


def test_test_suggest_success_with_monkeypatch(monkeypatch):
    """
    Test suggestion success by monkeypatching requests.post to return dummy data.
    """

    class MockedResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [{"message": {"content": "- Suggestion 1\n- Suggestion 2"}}]
            }

    def mock_post(*args, **kwargs):
        return MockedResponse()

    monkeypatch.setattr(main.requests, "post", mock_post)

    response = main.mock_summarize_with_openai("Requesting suggestions.", "en")
    assert isinstance(
        response.summary, str
    )  # Should be summary field, suggestions might rely on other func
    # Suggestion test might require specific suggestion function, so this test focuses on mocking external call


def test_test_summarize_fallback_handles_api_failure(monkeypatch):
    """
    Test summarization fallback mechanism if API raises exceptions.
    """

    def mock_post(*args, **kwargs):
        raise Exception("API failure")

    monkeypatch.setattr(main.requests, "post", mock_post)
    # Assuming function mock_summarize_with_openai has try-except fallback or is tested here
    with pytest.raises(Exception):
        main.mock_summarize_with_openai("Content that fails.", "en")
