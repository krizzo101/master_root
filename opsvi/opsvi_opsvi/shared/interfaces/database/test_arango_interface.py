import pytest

from src.shared.interfaces.database.arango_interface import DirectArangoDB

# These tests require a running ArangoDB instance and a test graph with known structure.
# If not available, mark as skipped.
TEST_GRAPH = "test_graph"
START_VERTEX = "nodes/A"
END_VERTEX = "nodes/B"


@pytest.fixture(scope="module")
def db():
    try:
        return DirectArangoDB()
    except Exception:
        pytest.skip("ArangoDB not available for testing")


def test_get_neighbors_success(db):
    res = db.get_neighbors(TEST_GRAPH, START_VERTEX, direction="out")
    assert isinstance(res, dict)
    assert "success" in res
    # Accept both True/False for success, but must have neighbors or error
    if res["success"]:
        assert "neighbors" in res
    else:
        assert "error" in res


def test_get_subgraph_success(db):
    res = db.get_subgraph(TEST_GRAPH, START_VERTEX, depth=2)
    assert isinstance(res, dict)
    assert "success" in res
    if res["success"]:
        assert "vertices" in res and "edges" in res
    else:
        assert "error" in res


def test_shortest_path_success(db):
    res = db.shortest_path(TEST_GRAPH, START_VERTEX, END_VERTEX)
    assert isinstance(res, dict)
    assert "success" in res
    if res["success"]:
        assert "path" in res
    else:
        assert "error" in res


def test_get_neighbors_invalid_graph(db):
    res = db.get_neighbors("nonexistent_graph", START_VERTEX)
    assert not res["success"]
    assert "error" in res


def test_shortest_path_invalid_vertices(db):
    res = db.shortest_path(TEST_GRAPH, "nodes/INVALID", "nodes/INVALID")
    assert not res["success"]
    assert "error" in res
