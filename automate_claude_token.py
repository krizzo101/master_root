#!/usr/bin/env python3
import os
import re
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class TokenCaptureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        if "token" in query_params:
            self.server.captured_token = query_params["token"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Token captured! You can close this window.</h1></body></html>"
            )
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Waiting for token...</h1></body></html>")

    def log_message(self, format, *args):
        pass


def capture_token_from_terminal():
    """
    Method 1: Capture token directly from terminal output
    """
    print("Starting Claude token setup...")

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
                    token_match = re.search(
                        r"CLAUDE_CODE_TOKEN[=:\s]+([a-zA-Z0-9_\-]+)", line
                    )
                    if token_match:
                        token = token_match.group(1)

                    # Also check for "Your token is:" pattern
                    token_match2 = re.search(
                        r"token[:\s]+([a-zA-Z0-9_\-]+)", line, re.IGNORECASE
                    )
                    if token_match2:
                        token = token_match2.group(1)

        # Start reading output in a thread
        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
        output_thread.start()

        # Wait for process to complete
        process.wait(timeout=120)
        output_thread.join(timeout=5)

        if token:
            return token

        # Try to extract token from full output
        full_output = "".join(output_lines)
        token_match = re.search(
            r"CLAUDE_CODE_TOKEN[=:\s]+([a-zA-Z0-9_\-]+)", full_output
        )
        if token_match:
            return token_match.group(1)

    except subprocess.TimeoutExpired:
        print("\nTimeout waiting for token setup")
        process.kill()
    except Exception as e:
        print(f"\nError: {e}")

    return None


def capture_token_with_server():
    """
    Method 2: Start local server to capture OAuth callback
    """
    print("Starting local server to capture OAuth callback...")

    # Start local server on port 9876
    server = HTTPServer(("localhost", 9876), TokenCaptureHandler)
    server.captured_token = None

    # Run server in thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print("Local server running on http://localhost:9876")
    print("Starting Claude token setup...")

    # Start the claude setup-token process
    process = subprocess.Popen(
        ["claude", "setup-token"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Monitor for authorization URL
    for line in iter(process.stdout.readline, ""):
        print(line, end="")
        if "http" in line.lower():
            url_match = re.search(r"(https?://[^\s]+)", line)
            if url_match:
                auth_url = url_match.group(1)
                print(f"\nOpening browser to: {auth_url}")
                webbrowser.open(auth_url)

    # Wait for token capture (max 2 minutes)
    timeout = 120
    start_time = time.time()

    while server.captured_token is None and (time.time() - start_time) < timeout:
        time.sleep(1)

    server.shutdown()

    if server.captured_token:
        return server.captured_token

    return None


def save_token_to_env(token):
    """Save token to .env file or export it"""
    env_file = os.path.join(os.path.expanduser("~"), ".claude_token")

    with open(env_file, "w") as f:
        f.write(f"export CLAUDE_CODE_TOKEN={token}\n")

    print(f"\nToken saved to {env_file}")
    print(f"To use it, run: source {env_file}")
    print(f"Or add to your shell profile: echo 'source {env_file}' >> ~/.bashrc")

    # Also create a .env file in current directory
    with open(".env", "a") as f:
        f.write(f"\nCLAUDE_CODE_TOKEN={token}\n")
    print(f"Token also appended to .env in current directory")


def main():
    print("Claude Token Automation Script")
    print("=" * 40)

    # Try method 1 first
    token = capture_token_from_terminal()

    if not token:
        print("\nMethod 1 failed, trying OAuth server method...")
        token = capture_token_with_server()

    if token:
        print(f"\n✓ Successfully captured token: {token[:10]}...")
        print(f"\nFull token: CLAUDE_CODE_TOKEN={token}")

        # Save token
        save_token_to_env(token)

        # Export for current session
        os.environ["CLAUDE_CODE_TOKEN"] = token
        print("\n✓ Token exported to current environment")

        return 0
    else:
        print("\n✗ Failed to capture token")
        print("Please run 'claude setup-token' manually")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
