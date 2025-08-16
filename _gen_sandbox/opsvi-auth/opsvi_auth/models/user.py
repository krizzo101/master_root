"""User model for opsvi-auth."""
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
