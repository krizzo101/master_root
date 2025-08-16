import importlib


def test_import_graph_client_module():
    assert importlib.import_module("opsvi_data.graph.client")


def test_import_vector_chroma_module():
    assert importlib.import_module("opsvi_data.vector.chroma_client")
