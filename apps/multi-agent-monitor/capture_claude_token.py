#!/usr/bin/env python3
"""
Claude Token Capture and Secure Storage
Automates the claude setup-token process and stores tokens in encrypted storage
"""
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from src.orchestration.secrets_manager import TokenSecretsManager


class ClaudeTokenCapture:
    def __init__(self):
        self.token = None
        self.manager = TokenSecretsManager(app_root=Path(__file__).parent)

    def capture_token_from_terminal(self):
        """
        Capture token directly from terminal output
        """
        print("Starting Claude token setup...")
        print("Please complete the authorization in your browser when prompted...")
        print("-" * 60)

        try:
            process = subprocess.Popen(
                ["claude", "setup-token"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            token = None
            output_lines = []

            def read_output():
                nonlocal token
                for line in iter(process.stdout.readline, ""):
                    if line:
                        output_lines.append(line)
                        print(line, end="")

                        # Look for token patterns in output
                        # Pattern 1: CLAUDE_CODE_TOKEN=xxx or CLAUDE_CODE_TOKEN: xxx
                        token_match = re.search(
                            r"CLAUDE_CODE_TOKEN[=:\s]+([a-zA-Z0-9_\-]+)", line
                        )
                        if token_match:
                            token = token_match.group(1)

                        # Pattern 2: Just the token if it starts with sk-ant-
                        token_match2 = re.search(r"(sk-ant-[a-zA-Z0-9_\-]+)", line)
                        if token_match2:
                            token = token_match2.group(1)

                        # Pattern 3: "Your token is:" pattern
                        token_match3 = re.search(
                            r"token[:\s]+([a-zA-Z0-9_\-]+)", line, re.IGNORECASE
                        )
                        if token_match3 and token_match3.group(1).startswith("sk-ant-"):
                            token = token_match3.group(1)

            def read_stderr():
                for line in iter(process.stderr.readline, ""):
                    if line:
                        print(line, end="", file=sys.stderr)

            # Start reading output in threads
            output_thread = threading.Thread(target=read_output)
            output_thread.daemon = True
            output_thread.start()

            stderr_thread = threading.Thread(target=read_stderr)
            stderr_thread.daemon = True
            stderr_thread.start()

            # Wait for process to complete (max 2 minutes)
            process.wait(timeout=120)
            output_thread.join(timeout=5)
            stderr_thread.join(timeout=5)

            if token:
                self.token = token
                return True

            # Try to extract token from full output
            full_output = "".join(output_lines)

            # Try various patterns
            patterns = [
                r"CLAUDE_CODE_TOKEN[=:\s]+([a-zA-Z0-9_\-]+)",
                r"(sk-ant-[a-zA-Z0-9_\-]+)",
                r"token[:\s]+([a-zA-Z0-9_\-]+)",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, full_output, re.IGNORECASE)
                for match in matches:
                    if match.startswith("sk-ant-") and len(match) > 50:
                        self.token = match
                        return True

        except subprocess.TimeoutExpired:
            print("\n⚠️  Timeout waiting for token setup (2 minutes)")
            print("The browser authorization may still be pending.")
            process.kill()
        except FileNotFoundError:
            print("\n❌ Error: 'claude' command not found.")
            print("Please ensure Claude CLI is installed and in your PATH.")
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

        return False

    def find_next_available_token_number(self):
        """Find the next available token number"""
        existing_tokens = self.manager.list_tokens()

        # Convert to integers (handle 'default' case)
        token_numbers = []
        for t in existing_tokens:
            if t.isdigit():
                token_numbers.append(int(t))

        if not token_numbers:
            return 1

        # Find the next available number
        return max(token_numbers) + 1

    def save_token_to_secure_storage(self):
        """Save captured token to encrypted storage"""
        if not self.token:
            print("\n❌ No token to save")
            return False

        # Validate token format
        if not self.token.startswith("sk-ant-") or len(self.token) < 50:
            print(f"\n⚠️  Warning: Token doesn't look like a valid Claude token")
            print(f"Token: {self.token[:20]}...")
            response = input("Save anyway? (y/n): ")
            if response.lower() != "y":
                return False

        # Find next available token number
        next_num = self.find_next_available_token_number()

        # Save to encrypted storage
        try:
            self.manager.add_token(next_num, self.token)
            print(f"\n✅ Token successfully saved as CLAUDE_CODE_TOKEN{next_num}")

            # Show current token summary
            all_tokens = self.manager.list_tokens()
            print(f"\n📊 Token Storage Summary:")
            print(f"   Total tokens: {len(all_tokens)}")
            print(
                f"   Token numbers: {', '.join(sorted(all_tokens, key=lambda x: int(x) if x.isdigit() else 0))}"
            )

            # Validate all tokens
            validation = self.manager.validate_tokens()
            invalid = [k for k, v in validation.items() if not v]
            if invalid:
                print(f"   ⚠️  Invalid tokens: {', '.join(invalid)}")
            else:
                print(f"   ✅ All tokens validated successfully")

            return True

        except Exception as e:
            print(f"\n❌ Error saving token: {e}")
            return False

    def cleanup_new_keys_file(self):
        """Remove new_keys.txt if all keys are stored"""
        new_keys_file = Path(__file__).parent / ".secrets" / "new_keys.txt"

        if new_keys_file.exists():
            # Check if the keys in new_keys.txt are already stored
            with open(new_keys_file, "r") as f:
                new_keys = [line.strip() for line in f if line.strip()]

            stored_tokens = self.manager.get_all_tokens()
            stored_values = list(stored_tokens.values())

            all_stored = all(key in stored_values for key in new_keys)

            if all_stored:
                new_keys_file.unlink()
                print(
                    f"\n🧹 Removed new_keys.txt (all {len(new_keys)} keys were already stored)"
                )

    def run(self, dry_run=False):
        """Main execution flow"""
        print("=" * 60)
        print("Claude Token Capture with Secure Storage")
        if dry_run:
            print("🔬 DRY RUN MODE - Will not save to encrypted storage")
        print("=" * 60)

        # Show current status
        existing_tokens = self.manager.list_tokens()
        if existing_tokens:
            print(f"\n📦 Currently stored tokens: {len(existing_tokens)}")
            print(
                f"   Numbers: {', '.join(sorted(existing_tokens, key=lambda x: int(x) if x.isdigit() else 0))}"
            )

        # Clean up new_keys.txt if needed (only if not dry run)
        if not dry_run:
            self.cleanup_new_keys_file()

        print("\n" + "=" * 60)

        # Capture token
        if self.capture_token_from_terminal():
            print("\n" + "=" * 60)
            print("✅ Token captured successfully!")
            print(f"Token: {self.token[:20]}...{self.token[-10:]}")

            if dry_run:
                print("\n🔬 DRY RUN - Token captured but NOT saved")
                print(f"Full token for verification:")
                print(f"CLAUDE_CODE_TOKEN={self.token}")
                print("\nTo save this token, run without --dry-run flag")
                return 0

            # Save to secure storage
            if self.save_token_to_secure_storage():
                print("\n🔐 Token securely stored in encrypted storage")
                print(f"Location: {self.manager.tokens_file}")

                # Export to environment for current session
                os.environ[
                    f"CLAUDE_CODE_TOKEN{self.find_next_available_token_number()-1}"
                ] = self.token
                print("\n✅ Token exported to current environment")

                return 0
            else:
                print("\n❌ Failed to save token to secure storage")
                return 1
        else:
            print("\n" + "=" * 60)
            print("❌ Failed to capture token")
            print("\nPossible issues:")
            print("  1. Browser authorization was cancelled")
            print("  2. The claude CLI is not installed")
            print("  3. Network connectivity issues")
            print("\nYou can run 'claude setup-token' manually and then use:")
            print(f"  python {__file__} --add <token_value>")
            return 1


def main():
    """Main entry point with CLI support"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Capture and store Claude tokens securely"
    )
    parser.add_argument(
        "--add", metavar="TOKEN", help="Add a token directly without capture"
    )
    parser.add_argument("--list", action="store_true", help="List stored token numbers")
    parser.add_argument(
        "--validate", action="store_true", help="Validate stored tokens"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Remove new_keys.txt if redundant"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Test token capture without saving"
    )

    args = parser.parse_args()

    if args.add:
        # Direct token addition
        manager = TokenSecretsManager(app_root=Path(__file__).parent)
        next_num = len(manager.list_tokens()) + 1

        # Find next available number
        existing = manager.list_tokens()
        token_numbers = [int(t) for t in existing if t.isdigit()]
        if token_numbers:
            next_num = max(token_numbers) + 1
        else:
            next_num = 1

        manager.add_token(next_num, args.add)
        return 0

    elif args.list:
        manager = TokenSecretsManager(app_root=Path(__file__).parent)
        tokens = manager.list_tokens()
        if tokens:
            print(
                f"Stored tokens: {', '.join(sorted(tokens, key=lambda x: int(x) if x.isdigit() else 0))}"
            )
            print(f"Total: {len(tokens)} tokens")
        else:
            print("No tokens stored")
        return 0

    elif args.validate:
        manager = TokenSecretsManager(app_root=Path(__file__).parent)
        results = manager.validate_tokens()
        for key, valid in sorted(results.items()):
            status = "✅" if valid else "❌"
            print(f"{status} {key}")
        return 0

    elif args.cleanup:
        capture = ClaudeTokenCapture()
        capture.cleanup_new_keys_file()
        return 0

    else:
        # Run token capture
        capture = ClaudeTokenCapture()
        return capture.run(dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
