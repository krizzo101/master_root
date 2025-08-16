"""Graph visualization renderers.

This module provides renderer classes for graph-based visualizations.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from proj_mapper.output.visualization.base import VisualizationConfig

# Configure logging
logger = logging.getLogger(__name__)


class GraphRenderer:
    """Base class for graph-based visualization renderers."""

    def __init__(self, config: VisualizationConfig):
        """Initialize the renderer.

        Args:
            config: The visualization configuration
        """
        self.config = config

    def render(self, graph_data: Dict[str, Any], output_path: Path) -> None:
        """Render a graph visualization.

        Args:
            graph_data: The graph data to visualize
            output_path: Path to save the visualization
        """
        raise NotImplementedError("Subclasses must implement render()")


class DotRenderer(GraphRenderer):
    """Renderer for Graphviz DOT format."""

    def render(self, graph_data: Dict[str, Any], output_path: Path) -> None:
        """Render a graph in DOT format.

        Args:
            graph_data: The graph data to visualize
            output_path: Path to save the visualization
        """
        # Create DOT file content
        dot_content = ["digraph G {"]

        # Add graph attributes based on theme
        if self.config.theme == "dark":
            dot_content.extend([
                '  bgcolor="#222222";',
                '  node [style=filled, fillcolor="#333333", fontcolor="#FFFFFF"];',
                '  edge [color="#56B4E9"];'
            ])

        # Add nodes
        for node in graph_data.get("nodes", []):
            node_id = node["id"]
            label = node.get("label", node_id)
            node_type = node.get("type", "unknown")

            # Customize node appearance based on type
            if node_type == "code":
                color = "#0072B2"
            elif node_type == "documentation":
                color = "#009E73"
            else:
                color = "#333333"

            dot_content.append(f'  "{node_id}" [label="{label}", fillcolor="{color}"];')

        # Add edges
        for edge in graph_data.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            label = edge.get("label", "")
            weight = edge.get("weight", 1.0)

            if weight >= self.config.min_confidence:
                if self.config.include_weights:
                    dot_content.append(f'  "{source}" -> "{target}" [label="{label}\\n{weight:.2f}"];')
                else:
                    dot_content.append(f'  "{source}" -> "{target}" [label="{label}"];')

        dot_content.append("}")

        # Write DOT file
        with open(output_path, "w") as f:
            f.write("\n".join(dot_content))


class HtmlRenderer(GraphRenderer):
    """Renderer for HTML format."""

    def render(self, graph_data: Dict[str, Any], output_path: Path) -> None:
        """Render a graph in HTML format.

        Args:
            graph_data: The graph data to visualize
            output_path: Path to save the visualization
        """
        # Try rich SVG via graphviz if available and 'dot' exists.
        try:
            import shutil
            dot_path = shutil.which("dot")
            if dot_path is None:
                raise RuntimeError("Graphviz 'dot' binary not found")

            from graphviz import Source

            # Create DOT file content
            dot_content = ["digraph G {"]

            # Add graph attributes based on theme
            if self.config.theme == "dark":
                dot_content.extend([
                    '  bgcolor="#222222";',
                    '  node [style=filled, fillcolor="#333333", fontcolor="#FFFFFF"];',
                    '  edge [color="#56B4E9"];'
                ])

            # Add nodes
            for node in graph_data.get("nodes", []):
                node_id = node["id"]
                label = node.get("label", node_id)
                node_type = node.get("type", "unknown")

                # Customize node appearance based on type
                if node_type == "code":
                    color = "#0072B2"
                elif node_type == "documentation":
                    color = "#009E73"
                else:
                    color = "#333333"

                dot_content.append(f'  "{node_id}" [label="{label}", fillcolor="{color}"];')

            # Add edges
            for edge in graph_data.get("edges", []):
                source = edge.get("source", "")
                target = edge.get("target", "")
                label = edge.get("label", "")
                weight = edge.get("weight", 1.0)

                if weight >= self.config.min_confidence and source and target:
                    if self.config.include_weights and label:
                        dot_content.append(f'  "{source}" -> "{target}" [label="{label}\\n{weight:.2f}"];')
                    elif label:
                        dot_content.append(f'  "{source}" -> "{target}" [label="{label}"];')
                    else:
                        dot_content.append(f'  "{source}" -> "{target}";')

            dot_content.append("}")

            # Create Graphviz source
            src = Source("\n".join(dot_content))

            # Render to SVG next to desired output, then wrap into HTML
            tmp_svg_base = output_path.with_suffix("")
            svg_file = Path(str(tmp_svg_base) + ".svg")
            src.render(tmp_svg_base, view=False, format='svg')

            # Read SVG content
            svg_data = svg_file.read_text(encoding="utf-8")

            # Write simple HTML wrapper embedding SVG inline
            html_content = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<title>Project Visualization</title>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<style>
  body {{ background: #111; color: #eee; margin: 0; padding: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; }}
  .container {{ padding: 12px; }}
  .svg-wrap {{ width: 100%; overflow: auto; background: #111; }}
  svg {{ width: 100%; height: auto; }}
</style>
</head>
<body>
  <div class=\"container\">
    <h1>Project Visualization (SVG)</h1>
    <div class=\"svg-wrap\">{svg_data}</div>
  </div>
</body>
</html>
"""
            output_path.write_text(html_content, encoding="utf-8")
            try:
                svg_file.unlink(missing_ok=True)
            except Exception:
                pass
            return
        except Exception as e:
            logger.warning(f"Graphviz SVG rendering unavailable, falling back to basic HTML: {e}")

        # Fallback: write a simple, dependency-free HTML listing
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Simple circular layout
        width, height = 1200, 900
        cx, cy = width // 2, height // 2
        radius = int(min(width, height) * 0.38)
        n = max(1, len(nodes))

        # Map node id -> (x, y)
        positions: dict[str, tuple[float, float]] = {}
        for idx, node in enumerate(nodes):
            angle = (2.0 * 3.1415926535 * idx) / n
            x = cx + radius * (1.0 * __import__("math").cos(angle))
            y = cy + radius * (1.0 * __import__("math").sin(angle))
            positions[str(node.get("id", idx))] = (x, y)

        def esc(s: str) -> str:
            return (
                str(s)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

        # Build SVG elements
        svg_edges: list[str] = []
        for e in edges:
            s = str(e.get("source", ""))
            t = str(e.get("target", ""))
            if s in positions and t in positions:
                (x1, y1) = positions[s]
                (x2, y2) = positions[t]
                svg_edges.append(
                    f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                    f'style="stroke:#56B4E9;stroke-width:1;opacity:0.7" />'
                )

        svg_nodes: list[str] = []
        for node in nodes:
            nid = str(node.get("id", ""))
            label = esc(node.get("label", nid))
            ntype = node.get("type", "code")
            color = "#0072B2" if ntype == "code" else ("#009E73" if ntype == "documentation" else "#888888")
            (x, y) = positions.get(nid, (cx, cy))
            svg_nodes.append(
                f'<g transform="translate({x:.1f},{y:.1f})">'
                f'<circle r="8" fill="{color}" stroke="#222" stroke-width="1" />'
                f'<text x="12" y="4" font-size="12" fill="#eee">{label}</text>'
                f"</g>"
            )

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="background:#111">'
            + "".join(svg_edges)
            + "".join(svg_nodes)
            + "</svg>"
        )

        html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<title>Project Visualization</title>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<style>
  body {{ background: #111; color: #eee; margin: 0; padding: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; }}
  .container {{ padding: 12px; }}
  .svg-wrap {{ width: 100%; overflow: auto; background: #111; }}
  svg {{ width: 100%; height: auto; }}
  .legend {{ font-size: 12px; opacity: 0.9; }}
  .legend span {{ display: inline-block; margin-right: 14px; }}
  .dot {{ width: 10px; height: 10px; display: inline-block; border-radius: 50%; margin-right: 6px; vertical-align: middle; }}
  .code {{ background: #0072B2; }}
  .doc {{ background: #009E73; }}
  .other {{ background: #888888; }}
  h1 {{ margin: 8px 0 12px 0; }}
  p.note {{ color: #bbb; }}
</style>
<body>
  <div class=\"container\">
    <h1>Project Visualization (fallback)</h1>
    <div class=\"legend\">
      <span><span class=\"dot code\"></span>Code</span>
      <span><span class=\"dot doc\"></span>Docs</span>
      <span><span class=\"dot other\"></span>Other</span>
    </div>
    <div class=\"svg-wrap\">{svg}</div>
    <p class=\"note\">Fallback SVG renderer is in use (no Graphviz). Install Graphviz for richer layout.</p>
  </div>
</body>
</html>
"""
        output_path.write_text(html, encoding="utf-8")
