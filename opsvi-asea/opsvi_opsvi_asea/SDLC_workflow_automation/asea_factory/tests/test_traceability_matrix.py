from asea_factory.utils.traceability_matrix import generate_traceability_matrix


def test_generate_traceability_matrix():
    requirements = [{"id": "req-1"}, {"id": "req-2"}]
    architecture = {"id": "arch-1"}
    code = [
        {"id": "code-1", "requirements": ["req-1"]},
        {"id": "code-2", "requirements": ["req-2"]},
    ]
    tests = [
        {"id": "test-1", "requirements": ["req-1"]},
        {"id": "test-2", "requirements": ["req-2"]},
    ]
    docs = [{"id": "doc-1", "requirements": ["req-1", "req-2"]}]
    matrix = generate_traceability_matrix(requirements, architecture, code, tests, docs)
    assert matrix is not None
    assert "req-1" in matrix.mapping
    assert "req-2" in matrix.mapping
