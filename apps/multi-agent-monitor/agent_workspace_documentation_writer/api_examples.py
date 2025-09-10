"""
API Usage Examples
"""

import json

import requests

BASE_URL = "http://localhost:8000"

# Health Check
response = requests.get(f"{BASE_URL}/health")
print("Health:", response.json())

# Create a task
new_task = {
    "title": "Complete API documentation",
    "description": "Write comprehensive docs for all endpoints",
    "priority": "high",
    "status": "in_progress",
}

response = requests.post(f"{BASE_URL}/tasks", json=new_task)
created_task = response.json()
print("Created:", created_task)

# Get task by ID
task_id = created_task["id"]
response = requests.get(f"{BASE_URL}/tasks/{task_id}")
print("Retrieved:", response.json())

# Update task
update_data = {"title": "Complete API documentation", "status": "completed"}
response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data)
print("Updated:", response.json())

# List all tasks
response = requests.get(f"{BASE_URL}/tasks")
print("All tasks:", response.json())

# Filter tasks by status
response = requests.get(f"{BASE_URL}/tasks?status=completed")
print("Completed tasks:", response.json())

# Delete task
response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
print("Deleted:", response.status_code)
