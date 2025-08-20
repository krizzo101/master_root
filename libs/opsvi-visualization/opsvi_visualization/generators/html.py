"""HTML format generator for visualizations"""

import json
from typing import Any, Dict


class HtmlGenerator:
    """Generates HTML visualizations"""

    def __init__(self):
        self.data = {}

    def set_data(self, data: Dict[str, Any]):
        """Set visualization data"""
        self.data = data

    def generate(self) -> str:
        """Generate HTML with embedded visualization"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Project Visualization</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .node {{ padding: 10px; margin: 5px; border: 1px solid #ccc; }}
        .edge {{ color: #666; }}
    </style>
</head>
<body>
    <h1>Project Structure Visualization</h1>
    <div id="visualization">
        <pre>{json.dumps(self.data, indent=2)}</pre>
    </div>
</body>
</html>"""
        return html
