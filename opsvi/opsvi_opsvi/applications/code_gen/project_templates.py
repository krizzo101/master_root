"""Project templates and type detection for code generation."""

import logging
from enum import Enum
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """Supported project types for code generation."""

    CLI_TOOL = "cli_tool"
    WEB_API = "web_api"
    DATA_PROCESSOR = "data_processor"
    WEB_APP = "web_app"
    SIMPLE_SCRIPT = "simple_script"


@dataclass
class ProjectTemplate:
    """Template definition for a project type."""

    project_type: ProjectType
    files: Dict[str, str]  # filename -> content
    dependencies: List[str]
    test_files: Dict[str, str]  # test filename -> content


# CLI Tool Template
CLI_TOOL_TEMPLATE = ProjectTemplate(
    project_type=ProjectType.CLI_TOOL,
    files={
        "main.py": '''#!/usr/bin/env python3
"""Command-line tool."""
import argparse
import logging
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CLI Tool")
    parser.add_argument("input", help="Input file or text")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)
    logger.info(f"Processing: {args.input}")

    # Process input
    result = f"Processed: {args.input}"

    if args.output:
        Path(args.output).write_text(result)
        logger.info(f"Output written to: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
''',
        "requirements.txt": "# Add your dependencies here\\n",
    },
    dependencies=["click", "rich"],
    test_files={
        "test_main.py": '''import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """Test CLI help output."""
    result = subprocess.run([sys.executable, "main.py", "--help"],
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert "CLI Tool" in result.stdout


def test_cli_basic_usage(tmp_path):
    """Test basic CLI usage."""
    output_file = tmp_path / "output.txt"
    result = subprocess.run([
        sys.executable, "main.py", "test_input",
        "--output", str(output_file)
    ], capture_output=True, text=True)

    assert result.returncode == 0
    assert output_file.exists()
    assert "Processed: test_input" in output_file.read_text()
''',
    },
)

# Web API Template
WEB_API_TEMPLATE = ProjectTemplate(
    project_type=ProjectType.WEB_API,
    files={
        "main.py": '''"""FastAPI web application."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn


app = FastAPI(title="Web API", version="1.0.0")


class Item(BaseModel):
    """Item model."""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None


# In-memory storage (replace with database in production)
items: List[Item] = []
next_id = 1


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Web API is running"}


@app.get("/items", response_model=List[Item])
async def get_items():
    """Get all items."""
    return items


@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item."""
    global next_id
    item.id = next_id
    next_id += 1
    items.append(item)
    return item


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get item by ID."""
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
        "requirements.txt": "fastapi>=0.104.0\\nuvicorn[standard]>=0.24.0\\npydantic>=2.0.0\\n",
    },
    dependencies=["fastapi", "uvicorn[standard]", "pydantic"],
    test_files={
        "test_api.py": '''from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Web API is running"}


def test_create_and_get_item():
    """Test creating and retrieving an item."""
    # Create item
    item_data = {"name": "Test Item", "description": "A test item"}
    response = client.post("/items", json=item_data)
    assert response.status_code == 200
    created_item = response.json()
    assert created_item["name"] == "Test Item"
    assert created_item["id"] == 1

    # Get item
    response = client.get(f"/items/{created_item['id']}")
    assert response.status_code == 200
    assert response.json() == created_item


def test_get_nonexistent_item():
    """Test getting non-existent item."""
    response = client.get("/items/999")
    assert response.status_code == 404
''',
    },
)

# Data Processor Template
DATA_PROCESSOR_TEMPLATE = ProjectTemplate(
    project_type=ProjectType.DATA_PROCESSOR,
    files={
        "data_processor.py": '''#!/usr/bin/env python3
"""Data processing application."""
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import argparse


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


class DataProcessor:
    """Generic data processor for CSV/JSON files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_csv(self, input_file: Path, output_file: Path) -> None:
        """Process CSV file."""
        self.logger.info(f"Processing CSV: {input_file}")

        processed_data = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Example processing: convert strings to uppercase
                processed_row = {k: v.upper() if isinstance(v, str) else v
                               for k, v in row.items()}
                processed_data.append(processed_row)

        with open(output_file, 'w', encoding='utf-8') as f:
            if processed_data:
                writer = csv.DictWriter(f, fieldnames=processed_data[0].keys())
                writer.writeheader()
                writer.writerows(processed_data)

        self.logger.info(f"Processed {len(processed_data)} records")

    def process_json(self, input_file: Path, output_file: Path) -> None:
        """Process JSON file."""
        self.logger.info(f"Processing JSON: {input_file}")

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Example processing: add timestamp and count
        if isinstance(data, list):
            processed_data = {
                "processed_count": len(data),
                "data": data
            }
        else:
            processed_data = {
                "processed_count": 1,
                "data": data
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2)

        self.logger.info("JSON processing completed")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Data Processor")
    parser.add_argument("input", help="Input file (CSV or JSON)")
    parser.add_argument("output", help="Output file")
    parser.add_argument("--format", choices=["csv", "json"],
                       help="Input format (auto-detected if not specified)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()
    setup_logging(args.verbose)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist")
        return

    # Auto-detect format if not specified
    format_type = args.format
    if not format_type:
        if input_path.suffix.lower() == '.csv':
            format_type = 'csv'
        elif input_path.suffix.lower() == '.json':
            format_type = 'json'
        else:
            print("Error: Cannot auto-detect format. Please specify --format")
            return

    processor = DataProcessor()

    try:
        if format_type == 'csv':
            processor.process_csv(input_path, output_path)
        elif format_type == 'json':
            processor.process_json(input_path, output_path)

        print(f"Processing completed: {output_path}")

    except Exception as e:
        logging.error(f"Processing failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
''',
        "requirements.txt": "# Data processing dependencies\\n",
    },
    dependencies=["pandas", "numpy"],
    test_files={
        "test_data_processor.py": '''import json
import csv
import tempfile
from pathlib import Path
from data_processor import DataProcessor, main
import subprocess
import sys


def test_csv_processing():
    """Test CSV file processing."""
    processor = DataProcessor()

    # Create test CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'age', 'city'])
        writer.writerow(['alice', '25', 'new york'])
        writer.writerow(['bob', '30', 'san francisco'])
        input_file = Path(f.name)

    # Process
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_file = Path(f.name)

    processor.process_csv(input_file, output_file)

    # Verify
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['name'] == 'ALICE'
        assert rows[0]['city'] == 'NEW YORK'

    # Cleanup
    input_file.unlink()
    output_file.unlink()


def test_json_processing():
    """Test JSON file processing."""
    processor = DataProcessor()

    # Create test JSON
    test_data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        input_file = Path(f.name)

    # Process
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = Path(f.name)

    processor.process_json(input_file, output_file)

    # Verify
    with open(output_file, 'r') as f:
        result = json.load(f)
        assert result['processed_count'] == 2
        assert len(result['data']) == 2

    # Cleanup
    input_file.unlink()
    output_file.unlink()


def test_cli_interface():
    """Test CLI interface."""
    # Create test file
    test_data = {"test": "data"}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        input_file = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name

    # Run CLI
    result = subprocess.run([
        sys.executable, 'data_processor.py', input_file, output_file
    ], capture_output=True, text=True)

    assert result.returncode == 0

    # Cleanup
    Path(input_file).unlink()
    Path(output_file).unlink()
''',
    },
)

# Web App Template
WEB_APP_TEMPLATE = ProjectTemplate(
    project_type=ProjectType.WEB_APP,
    files={
        "app.py": '''#!/usr/bin/env python3
"""Simple web application with HTML frontend."""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pathlib import Path
import os


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# In-memory data store (replace with database in production)
items = [
    {"id": 1, "name": "Sample Item 1", "description": "This is a sample item"},
    {"id": 2, "name": "Sample Item 2", "description": "Another sample item"},
]
next_id = 3


@app.route('/')
def home():
    """Home page showing all items."""
    return render_template('home.html', items=items)


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    """Add new item."""
    if request.method == 'POST':
        global next_id
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if name:
            new_item = {
                "id": next_id,
                "name": name,
                "description": description
            }
            items.append(new_item)
            next_id += 1
            return redirect(url_for('home'))

    return render_template('add_item.html')


@app.route('/api/items')
def api_items():
    """API endpoint to get all items."""
    return jsonify(items)


@app.route('/api/items', methods=['POST'])
def api_add_item():
    """API endpoint to add item."""
    global next_id
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({"error": "Name is required"}), 400

    new_item = {
        "id": next_id,
        "name": data['name'],
        "description": data.get('description', '')
    }
    items.append(new_item)
    next_id += 1

    return jsonify(new_item), 201


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "items_count": len(items)})


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)
''',
        "templates/base.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Web App{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
        .nav a:hover { text-decoration: underline; }
        .item { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .item h3 { margin: 0 0 10px 0; color: #333; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn:hover { background-color: #0056b3; }
        .alert { padding: 15px; margin: 15px 0; border-radius: 4px; }
        .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/">Home</a>
            <a href="/add">Add Item</a>
            <a href="/api/items">API</a>
        </div>
        {% block content %}{% endblock %}
    </div>
</body>
</html>""",
        "templates/home.html": """{% extends "base.html" %}

{% block title %}Home - Web App{% endblock %}

{% block content %}
<h1>Items List</h1>

<p><a href="/add" class="btn">Add New Item</a></p>

{% if items %}
    {% for item in items %}
    <div class="item">
        <h3>{{ item.name }}</h3>
        <p>{{ item.description or "No description" }}</p>
        <small>ID: {{ item.id }}</small>
    </div>
    {% endfor %}
{% else %}
    <p>No items found. <a href="/add">Add the first item</a>.</p>
{% endif %}
{% endblock %}""",
        "templates/add_item.html": """{% extends "base.html" %}

{% block title %}Add Item - Web App{% endblock %}

{% block content %}
<h1>Add New Item</h1>

<form method="POST">
    <div class="form-group">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required>
    </div>

    <div class="form-group">
        <label for="description">Description:</label>
        <textarea id="description" name="description" rows="4"></textarea>
    </div>

    <button type="submit" class="btn">Add Item</button>
    <a href="/" class="btn" style="background-color: #6c757d;">Cancel</a>
</form>
{% endblock %}""",
        "requirements.txt": "flask>=2.3.0\\nwerkzeug>=2.3.0\\n",
    },
    dependencies=["flask", "werkzeug"],
    test_files={
        "test_app.py": '''import pytest
from app import app
import json


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Test home page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Items List' in response.data


def test_add_item_page(client):
    """Test add item page loads."""
    response = client.get('/add')
    assert response.status_code == 200
    assert b'Add New Item' in response.data


def test_api_items(client):
    """Test API items endpoint."""
    response = client.get('/api/items')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) >= 2  # Sample items


def test_api_add_item(client):
    """Test API add item."""
    item_data = {"name": "Test Item", "description": "Test Description"}
    response = client.post('/api/items',
                          data=json.dumps(item_data),
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Test Item'
    assert 'id' in data


def test_health_endpoint(client):
    """Test health check."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'items_count' in data


def test_add_item_form(client):
    """Test adding item via form."""
    response = client.post('/add', data={
        'name': 'Form Test Item',
        'description': 'Added via form'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Form Test Item' in response.data
''',
    },
)

# Simple Script Template
SIMPLE_SCRIPT_TEMPLATE = ProjectTemplate(
    project_type=ProjectType.SIMPLE_SCRIPT,
    files={
        "script.py": '''#!/usr/bin/env python3
"""Simple Python script."""


def main() -> None:
    """Main function."""
    print("Hello from the generated script!")

    # Add your logic here
    result = 42
    print(f"The answer is: {result}")


if __name__ == "__main__":
    main()
''',
    },
    dependencies=[],
    test_files={
        "test_script.py": '''import script
import io
import sys


def test_main_output(capsys):
    """Test main function output."""
    script.main()
    captured = capsys.readouterr()
    assert "Hello from the generated script!" in captured.out
    assert "The answer is: 42" in captured.out
''',
    },
)


# Note: Project type detection has been moved to AI agents
# See code_gen.ai_agents.detect_project_type_with_ai() for intelligent project type detection

# Template registry
TEMPLATES: Dict[ProjectType, ProjectTemplate] = {
    ProjectType.CLI_TOOL: CLI_TOOL_TEMPLATE,
    ProjectType.WEB_API: WEB_API_TEMPLATE,
    ProjectType.DATA_PROCESSOR: DATA_PROCESSOR_TEMPLATE,
    ProjectType.WEB_APP: WEB_APP_TEMPLATE,
    ProjectType.SIMPLE_SCRIPT: SIMPLE_SCRIPT_TEMPLATE,
}


def get_template(project_type: ProjectType) -> ProjectTemplate:
    """Get template for project type."""
    return TEMPLATES.get(project_type, SIMPLE_SCRIPT_TEMPLATE)
