"""DOT format generator for visualizations"""


class DotGenerator:
    """Generates DOT format visualizations"""

    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, node_id: str, label: str, **attrs):
        """Add a node to the graph"""
        self.nodes.append({"id": node_id, "label": label, "attrs": attrs})

    def add_edge(self, from_id: str, to_id: str, **attrs):
        """Add an edge to the graph"""
        self.edges.append({"from": from_id, "to": to_id, "attrs": attrs})

    def generate(self) -> str:
        """Generate DOT format string"""
        lines = ["digraph G {"]

        # Add nodes
        for node in self.nodes:
            attrs = ", ".join(f'{k}="{v}"' for k, v in node["attrs"].items())
            lines.append(f'  "{node["id"]}" [label="{node["label"]}", {attrs}];')

        # Add edges
        for edge in self.edges:
            attrs = ", ".join(f'{k}="{v}"' for k, v in edge["attrs"].items())
            lines.append(f'  "{edge["from"]}" -> "{edge["to"]}" [{attrs}];')

        lines.append("}")
        return "\n".join(lines)
