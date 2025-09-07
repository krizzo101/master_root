#!/usr/bin/env python3
"""Sample Python code for demonstration purposes."""

import os
import sys
from typing import List, Dict, Optional


class UserManager:
    """Manages user operations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.users: Dict[str, Dict] = {}

    def create_user(self, username: str, email: str, password: str) -> bool:
        """Create a new user."""
        if username in self.users:
            return False

        # TODO: Hash password before storing
        self.users[username] = {
            "email": email,
            "password": password,  # Security issue: plain text password
            "created_at": "2025-01-15",
        }
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        if username not in self.users:
            return False

        # Security issue: plain text comparison
        return self.users[username]["password"] == password

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information."""
        return self.users.get(username)

    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        if username in self.users:
            del self.users[username]
            return True
        return False


def process_users(user_list: List[str]) -> List[Dict]:
    """Process a list of users."""
    results = []

    for user in user_list:
        try:
            # This could be optimized
            if len(user) > 0:
                results.append({"name": user, "status": "processed"})
        except Exception as e:
            print(f"Error processing user {user}: {e}")

    return results


def main():
    """Main function."""
    manager = UserManager("sqlite:///users.db")

    # Create some users
    manager.create_user("alice", "alice@example.com", "password123")
    manager.create_user("bob", "bob@example.com", "secret456")

    # Authenticate
    if manager.authenticate_user("alice", "password123"):
        print("Alice authenticated successfully")

    # Get user info
    user_info = manager.get_user_info("alice")
    if user_info:
        print(f"User info: {user_info}")


if __name__ == "__main__":
    main()

