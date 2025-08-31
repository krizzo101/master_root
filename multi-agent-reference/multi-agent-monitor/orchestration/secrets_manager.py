#!/usr/bin/env python3
"""
Secrets Manager for Multi-Agent Monitor
Secure storage and management of Claude Code tokens
"""

import getpass
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet


class TokenSecretsManager:
    """Manages Claude Code tokens with encryption at rest"""

    def __init__(self, app_root: Optional[Path] = None):
        """Initialize the secrets manager"""
        if app_root is None:
            app_root = Path(__file__).parent.parent.parent

        self.app_root = app_root
        self.secrets_dir = app_root / ".secrets"
        self.secrets_dir.mkdir(exist_ok=True, mode=0o700)  # Only owner can access

        # File paths
        self.tokens_file = self.secrets_dir / "tokens.encrypted"
        self.key_file = self.secrets_dir / ".key"
        self.plaintext_file = self.secrets_dir / "tokens.json"  # For easy editing

        # Initialize encryption
        self.cipher = self._get_or_create_cipher()

    def _get_or_create_cipher(self) -> Fernet:
        """Get existing cipher or create new one"""
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)  # Only owner can read

        return Fernet(key)

    def add_token(self, token_number: int, token_value: str):
        """Add or update a token"""
        tokens = self.load_tokens()
        tokens[f"CLAUDE_CODE_TOKEN{token_number}"] = token_value
        self.save_tokens(tokens)
        print(f"✅ Token {token_number} saved successfully")

    def add_tokens_bulk(self, tokens_dict: Dict[int, str]):
        """Add multiple tokens at once"""
        tokens = self.load_tokens()
        for num, value in tokens_dict.items():
            tokens[f"CLAUDE_CODE_TOKEN{num}"] = value
        self.save_tokens(tokens)
        print(f"✅ {len(tokens_dict)} tokens saved successfully")

    def load_tokens(self) -> Dict[str, str]:
        """Load tokens from encrypted storage"""
        # First check if plaintext file exists (for initial setup)
        if self.plaintext_file.exists():
            print("⚠️  Found plaintext tokens file - encrypting and removing...")
            with open(self.plaintext_file, "r") as f:
                tokens = json.load(f)

            # Save encrypted and remove plaintext
            self.save_tokens(tokens)
            self.plaintext_file.unlink()
            return tokens

        # Load from encrypted file
        if self.tokens_file.exists():
            with open(self.tokens_file, "rb") as f:
                encrypted_data = f.read()

            try:
                decrypted_data = self.cipher.decrypt(encrypted_data)
                tokens = json.loads(decrypted_data.decode())
                return tokens
            except Exception as e:
                print(f"❌ Error decrypting tokens: {e}")
                return {}

        return {}

    def save_tokens(self, tokens: Dict[str, str]):
        """Save tokens to encrypted storage"""
        # Encrypt and save
        json_data = json.dumps(tokens, indent=2)
        encrypted_data = self.cipher.encrypt(json_data.encode())

        with open(self.tokens_file, "wb") as f:
            f.write(encrypted_data)

        os.chmod(self.tokens_file, 0o600)  # Only owner can read

    def list_tokens(self) -> List[str]:
        """List available token numbers (not values)"""
        tokens = self.load_tokens()
        token_nums = []
        for key in sorted(tokens.keys()):
            if key.startswith("CLAUDE_CODE_TOKEN"):
                num = key.replace("CLAUDE_CODE_TOKEN", "")
                token_nums.append(num if num else "default")
        return token_nums

    def get_token(self, token_number: int) -> Optional[str]:
        """Get a specific token"""
        tokens = self.load_tokens()
        return tokens.get(f"CLAUDE_CODE_TOKEN{token_number}")

    def get_all_tokens(self) -> Dict[str, str]:
        """Get all tokens for environment export"""
        return self.load_tokens()

    def export_to_environment(self):
        """Export tokens to current environment"""
        tokens = self.load_tokens()
        for key, value in tokens.items():
            os.environ[key] = value
        print(f"✅ Exported {len(tokens)} tokens to environment")

    def import_from_environment(self):
        """Import tokens from current environment"""
        tokens = {}
        imported = 0

        # Check for primary token
        if "CLAUDE_CODE_TOKEN" in os.environ:
            tokens["CLAUDE_CODE_TOKEN"] = os.environ["CLAUDE_CODE_TOKEN"]
            imported += 1

        # Check for numbered tokens
        for i in range(1, 100):  # Check up to 100 tokens
            key = f"CLAUDE_CODE_TOKEN{i}"
            if key in os.environ:
                tokens[key] = os.environ[key]
                imported += 1

        if imported > 0:
            self.save_tokens(tokens)
            print(f"✅ Imported {imported} tokens from environment")
        else:
            print("ℹ️  No tokens found in environment")

    def validate_tokens(self) -> Dict[str, bool]:
        """Validate token format (basic check)"""
        tokens = self.load_tokens()
        results = {}

        for key, value in tokens.items():
            # Basic validation - Claude tokens start with sk-ant-
            is_valid = value.startswith("sk-ant-") and len(value) > 50
            results[key] = is_valid

        return results

    def interactive_setup(self):
        """Interactive token setup"""
        print(
            """
╔══════════════════════════════════════════════════════╗
║     CLAUDE CODE TOKEN SETUP                          ║
╚══════════════════════════════════════════════════════╝
"""
        )

        tokens = self.load_tokens()
        existing = len(tokens)

        if existing > 0:
            print(f"ℹ️  Found {existing} existing tokens")
            print(f"   Token numbers: {', '.join(self.list_tokens())}")

            if input("\nDo you want to add more tokens? (y/n): ").lower() != "y":
                return

        print("\nEnter tokens one at a time (or 'done' to finish):")
        print("Tokens should start with 'sk-ant-'")
        print()

        new_tokens = {}
        current_num = existing + 1

        while True:
            token = getpass.getpass(f"Token {current_num} (or 'done'): ").strip()

            if token.lower() == "done" or not token:
                break

            if not token.startswith("sk-ant-"):
                print("⚠️  Warning: Token doesn't start with 'sk-ant-'")
                if input("Use anyway? (y/n): ").lower() != "y":
                    continue

            new_tokens[current_num] = token
            current_num += 1
            print(f"✅ Token {current_num - 1} added")

        if new_tokens:
            self.add_tokens_bulk(new_tokens)
            print(f"\n✅ Added {len(new_tokens)} new tokens")

        # Show summary
        all_tokens = self.load_tokens()
        print(f"\n📊 Token Summary:")
        print(f"   Total tokens: {len(all_tokens)}")
        print(f"   Token numbers: {', '.join(self.list_tokens())}")

        # Validate
        validation = self.validate_tokens()
        invalid = [k for k, v in validation.items() if not v]
        if invalid:
            print(f"   ⚠️ Invalid tokens: {', '.join(invalid)}")

    def rotate_tokens(self):
        """Rotate encryption key (re-encrypt all tokens)"""
        tokens = self.load_tokens()

        # Generate new key
        old_key_file = self.key_file.with_suffix(".old")
        self.key_file.rename(old_key_file)

        # Create new cipher
        self.cipher = self._get_or_create_cipher()

        # Re-encrypt tokens
        self.save_tokens(tokens)

        # Remove old key
        old_key_file.unlink()

        print("✅ Token encryption key rotated successfully")


class TokenPoolIntegration:
    """Integration with the token pool manager"""

    def __init__(self, secrets_manager: TokenSecretsManager):
        self.secrets = secrets_manager

    def load_tokens_to_pool(self) -> List[str]:
        """Load tokens for pool usage"""
        tokens = self.secrets.get_all_tokens()
        token_list = []

        # Add primary token if exists
        if "CLAUDE_CODE_TOKEN" in tokens:
            token_list.append(tokens["CLAUDE_CODE_TOKEN"])

        # Add numbered tokens
        for i in range(1, 100):
            key = f"CLAUDE_CODE_TOKEN{i}"
            if key in tokens:
                token_list.append(tokens[key])

        return token_list

    def get_token_for_agent(self, agent_number: int) -> Optional[str]:
        """Get specific token for an agent"""
        tokens = self.load_tokens_to_pool()
        if agent_number <= len(tokens):
            return tokens[agent_number - 1]

        # Round-robin if more agents than tokens
        if tokens:
            return tokens[(agent_number - 1) % len(tokens)]

        return None


# CLI Interface
def main():
    """Command-line interface for token management"""
    manager = TokenSecretsManager()

    if len(sys.argv) == 1:
        # Interactive mode
        manager.interactive_setup()
        return

    command = sys.argv[1].lower()

    if command == "add":
        if len(sys.argv) < 4:
            print("Usage: python secrets_manager.py add <token_number> <token_value>")
            return

        token_num = int(sys.argv[2])
        token_value = sys.argv[3]
        manager.add_token(token_num, token_value)

    elif command == "list":
        tokens = manager.list_tokens()
        if tokens:
            print(f"Available tokens: {', '.join(tokens)}")
        else:
            print("No tokens stored")

    elif command == "validate":
        results = manager.validate_tokens()
        for key, valid in results.items():
            status = "✅" if valid else "❌"
            print(f"{status} {key}")

    elif command == "export":
        manager.export_to_environment()

    elif command == "import":
        manager.import_from_environment()

    elif command == "rotate":
        manager.rotate_tokens()

    elif command == "setup":
        manager.interactive_setup()

    else:
        print(
            f"""
Token Secrets Manager

Usage:
    python secrets_manager.py              # Interactive setup
    python secrets_manager.py setup        # Interactive setup
    python secrets_manager.py add <num> <token>  # Add token
    python secrets_manager.py list         # List token numbers
    python secrets_manager.py validate     # Validate tokens
    python secrets_manager.py export       # Export to environment
    python secrets_manager.py import       # Import from environment
    python secrets_manager.py rotate       # Rotate encryption key
"""
        )


if __name__ == "__main__":
    main()
