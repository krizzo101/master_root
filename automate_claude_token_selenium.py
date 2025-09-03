#!/usr/bin/env python3
"""
Advanced Claude token automation using Selenium for browser automation.
Requires: pip install selenium webdriver-manager
"""
import os
import re
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Please install required packages:")
    print("pip install selenium webdriver-manager")
    sys.exit(1)


class ClaudeTokenAutomator:
    def __init__(self, headless=False):
        self.headless = headless
        self.token = None
        self.auth_url = None

    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def capture_auth_url(self):
        """Run claude setup-token and capture the authorization URL"""
        print("Starting Claude setup-token process...")

        process = subprocess.Popen(
            ["claude", "setup-token"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Capture output to find auth URL
        for line in iter(process.stdout.readline, ""):
            print(line, end="")

            # Look for authorization URL
            if "http" in line.lower():
                url_match = re.search(r"(https?://[^\s]+)", line)
                if url_match and "auth" in url_match.group(1).lower():
                    self.auth_url = url_match.group(1).strip()
                    print(f"\nFound authorization URL: {self.auth_url}")
                    return True

            # Check if token is directly in output
            token_match = re.search(r"CLAUDE_CODE_TOKEN[=:\s]+([a-zA-Z0-9_\-]+)", line)
            if token_match:
                self.token = token_match.group(1)
                return True

        return False

    def automate_browser_auth(self):
        """Automate the browser authorization process"""
        if not self.auth_url:
            print("No authorization URL found")
            return False

        print("Opening browser for authorization...")
        self.setup_driver()

        try:
            # Navigate to auth URL
            self.driver.get(self.auth_url)
            time.sleep(2)

            # Wait for and click the Authorize button
            print("Looking for Authorize button...")

            # Try different possible selectors for the authorize button
            button_selectors = [
                "//button[contains(text(), 'Authorize')]",
                "//button[contains(text(), 'Allow')]",
                "//button[contains(text(), 'Accept')]",
                "//input[@type='submit' and @value='Authorize']",
                "//button[@type='submit']",
                "//a[contains(text(), 'Authorize')]",
            ]

            button_found = False
            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"Found button with selector: {selector}")
                    button.click()
                    button_found = True
                    break
                except:
                    continue

            if not button_found:
                print("Could not find Authorize button automatically")
                print("Please click Authorize manually in the browser...")
                # Wait for manual intervention
                time.sleep(30)

            # Wait for redirect back to localhost or token display
            print("Waiting for token...")
            time.sleep(5)

            # Check current URL for token
            current_url = self.driver.current_url
            if "token=" in current_url:
                token_match = re.search(r"token=([a-zA-Z0-9_\-]+)", current_url)
                if token_match:
                    self.token = token_match.group(1)
                    return True

            # Check page content for token
            page_source = self.driver.page_source
            token_match = re.search(
                r"CLAUDE_CODE_TOKEN[=:\s]+([a-zA-Z0-9_\-]+)", page_source
            )
            if token_match:
                self.token = token_match.group(1)
                return True

            # Try to find token in any visible text
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            token_match = re.search(r"([a-zA-Z0-9_\-]{40,})", body_text)
            if token_match:
                self.token = token_match.group(1)
                return True

        except Exception as e:
            print(f"Browser automation error: {e}")
            return False
        finally:
            self.driver.quit()

        return False

    def monitor_terminal_output(self):
        """Monitor terminal for token output after browser auth"""
        print("\nMonitoring terminal for token output...")

        # The token might appear in the terminal after browser auth
        timeout = 30
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if claude command outputs token
            result = subprocess.run(
                ["claude", "auth", "status"], capture_output=True, text=True
            )

            if "CLAUDE_CODE_TOKEN" in result.stdout:
                token_match = re.search(
                    r"CLAUDE_CODE_TOKEN[=:\s]+([a-zA-Z0-9_\-]+)", result.stdout
                )
                if token_match:
                    self.token = token_match.group(1)
                    return True

            time.sleep(2)

        return False

    def save_token(self):
        """Save the captured token"""
        if not self.token:
            return False

        # Save to home directory
        env_file = os.path.join(os.path.expanduser("~"), ".claude_token")
        with open(env_file, "w") as f:
            f.write(f"export CLAUDE_CODE_TOKEN={self.token}\n")

        print(f"\n✓ Token saved to {env_file}")

        # Save to current directory .env
        if os.path.exists(".env"):
            with open(".env", "a") as f:
                f.write(f"\nCLAUDE_CODE_TOKEN={self.token}\n")
        else:
            with open(".env", "w") as f:
                f.write(f"CLAUDE_CODE_TOKEN={self.token}\n")

        print(f"✓ Token saved to .env")

        # Export to current session
        os.environ["CLAUDE_CODE_TOKEN"] = self.token

        print(f"\n✓ Successfully captured and saved token!")
        print(f"Token: CLAUDE_CODE_TOKEN={self.token}")
        print(f"\nTo use in current shell: source {env_file}")

        return True

    def run(self):
        """Main automation flow"""
        print("Claude Token Selenium Automation")
        print("=" * 40)

        # Start claude setup-token in thread
        auth_thread = threading.Thread(target=self.capture_auth_url)
        auth_thread.start()

        # Wait for auth URL
        auth_thread.join(timeout=30)

        if self.token:
            # Token was captured directly from terminal
            self.save_token()
            return True

        if self.auth_url:
            # Automate browser
            if self.automate_browser_auth():
                self.save_token()
                return True

            # Try monitoring terminal after browser auth
            if self.monitor_terminal_output():
                self.save_token()
                return True

        print("\n✗ Failed to capture token automatically")
        print("Please run 'claude setup-token' manually")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Automate Claude token setup")
    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
    )
    args = parser.parse_args()

    automator = ClaudeTokenAutomator(headless=args.headless)
    success = automator.run()

    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
