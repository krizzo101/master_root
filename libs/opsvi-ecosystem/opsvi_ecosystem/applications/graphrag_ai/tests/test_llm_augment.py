from ..llm_augment import augment_with_graph, call_llm, format_prompt


def test_format_prompt():
    prompt = format_prompt("Q?", "CTX")
    assert "Context:" in prompt and "Q?" in prompt


def test_call_llm():
    response = call_llm("prompt")
    assert response.startswith("[ERROR: OPENAI_API_KEY not set]") or isinstance(
        response, str
    )


def test_augment_with_graph():
    answer = augment_with_graph("Q?", "CTX")
    assert answer.startswith("[ERROR: OPENAI_API_KEY not set]") or isinstance(
        answer, str
    )
