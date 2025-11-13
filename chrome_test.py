#!/usr/bin/env python3
r"""
Chrome Remote Debugging - X/Twitter Automation

First, launch Chrome with remote debugging:
  Linux:   google-chrome --remote-debugging-port=9222
  Mac:     /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
  Windows: chrome.exe --remote-debugging-port=9222

Or launch with a specific profile:
  google-chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def connect_to_chrome(debug_port=9222):
    """Connect to an already-running Chrome instance."""
    # For WSL2, use Windows host IP instead of localhost
    import os
    host = "127.0.0.1"
    if os.path.exists("/etc/resolv.conf"):
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if line.startswith("nameserver"):
                    host = line.split()[1]
                    break

    options = Options()
    options.add_experimental_option("debuggerAddress", f"{host}:{debug_port}")
    print(f"Connecting to Chrome at {host}:{debug_port}")

    driver = webdriver.Chrome(options=options)
    return driver


def post_to_x(driver, text):
    """Post a tweet on X/Twitter."""
    try:
        # Navigate to X if not already there
        if "x.com" not in driver.current_url and "twitter.com" not in driver.current_url:
            driver.get("https://x.com/home")
            time.sleep(2)

        # Wait for and click the tweet compose area
        # X/Twitter uses various selectors, these may need adjustment
        compose_selectors = [
            "//span[contains(text(), \"What is happening\")]",
            "//div[@data-testid='tweetTextarea_0']",
            "//div[@role='textbox'][@contenteditable='true']",
        ]

        compose_box = None
        for selector in compose_selectors:
            try:
                compose_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                compose_box.click()
                time.sleep(1)
                break
            except:
                continue

        if not compose_box:
            print("Could not find compose box. Make sure you're logged in.")
            return False

        # Find the actual text input area
        text_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']"))
        )

        # Type the tweet
        text_input.send_keys(text)
        print(f"Typed: {text}")

        # Optional: Find and click post button
        # post_button = driver.find_element(By.XPATH, "//button[@data-testid='tweetButtonInline']")
        # post_button.click()
        # print("Tweet posted!")

        print("Tweet ready to post (commented out actual posting for safety)")
        return True

    except Exception as e:
        print(f"Error posting: {e}")
        return False


def main():
    print("Connecting to Chrome on port 9222...")
    print("Make sure Chrome is running with: google-chrome --remote-debugging-port=9222")
    print()

    try:
        driver = connect_to_chrome()
        print(f"Connected! Current URL: {driver.current_url}")
        print(f"Current title: {driver.title}")
        print()

        # Navigate to Bing to test
        print("Navigating to bing.com...")
        driver.get("https://www.bing.com")
        time.sleep(2)
        print(f"Successfully navigated to: {driver.current_url}")
        print(f"Page title: {driver.title}")

        print("\nTest successful! Browser is under automation control.")
        print("The browser will remain open and connected.")
        print("Press Ctrl+C to disconnect (browser stays open).")

        # Keep script running
        input("\nPress Enter to disconnect...\n")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. Chrome is running with --remote-debugging-port=9222")
        print("2. You have selenium installed: pip install selenium")
        print("3. You have chromedriver installed and in PATH")


if __name__ == "__main__":
    main()
