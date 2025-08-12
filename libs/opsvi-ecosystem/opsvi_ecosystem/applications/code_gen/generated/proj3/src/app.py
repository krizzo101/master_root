#!/usr/bin/env python3
"""Simple web application with HTML frontend."""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pathlib import Path
import os


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# In-memory data store (replace with database in production)
items = [
    {"id": 1, "name": "Sample Item 1", "description": "This is a sample item"},
    {"id": 2, "name": "Sample Item 2", "description": "Another sample item"},
]
next_id = 3


@app.route("/")
def home():
    """Home page showing all items."""
    return render_template("home.html", items=items)


@app.route("/add", methods=["GET", "POST"])
def add_item():
    """Add new item."""
    if request.method == "POST":
        global next_id
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if name:
            new_item = {"id": next_id, "name": name, "description": description}
            items.append(new_item)
            next_id += 1
            return redirect(url_for("home"))

    return render_template("add_item.html")


@app.route("/api/items")
def api_items():
    """API endpoint to get all items."""
    return jsonify(items)


@app.route("/api/items", methods=["POST"])
def api_add_item():
    """API endpoint to add item."""
    global next_id
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    new_item = {
        "id": next_id,
        "name": data["name"],
        "description": data.get("description", ""),
    }
    items.append(new_item)
    next_id += 1

    return jsonify(new_item), 201


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "items_count": len(items)})


if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    app.run(debug=True, host="0.0.0.0", port=5000)
