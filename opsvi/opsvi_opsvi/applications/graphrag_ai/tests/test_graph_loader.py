import os
import tempfile

from ..graph_loader import load_graph_from_csv, load_graph_from_json


def test_load_graph_from_csv():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("A,B\nB,C\n")
        f.flush()
        G = load_graph_from_csv(f.name)
    os.unlink(f.name)
    assert set(G.nodes()) == {"A", "B", "C"}
    assert set(G.edges()) == {("A", "B"), ("B", "C")}


def test_load_graph_from_json():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write('{"A": ["B"], "B": ["C"]}')
        f.flush()
        G = load_graph_from_json(f.name)
    os.unlink(f.name)
    assert set(G.nodes()) == {"A", "B", "C"}
    assert set(G.edges()) == {("A", "B"), ("B", "C")}
