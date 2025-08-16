import networkx as nx

from ..graph_query import extract_subgraph, neighbors, shortest_path


def test_shortest_path():
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("B", "C")])
    path = shortest_path(G, "A", "C")
    assert path == ["A", "B", "C"]


def test_neighbors():
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("A", "C")])
    n = neighbors(G, "A")
    assert set(n) == {"B", "C"}


def test_extract_subgraph():
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
    sub = extract_subgraph(G, ["B", "C"])
    assert set(sub.nodes()) == {"B", "C"}
    assert set(sub.edges()) == {("B", "C")}
