"""
Pytest configuration and shared fixtures
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, MagicMock, AsyncMock


@pytest.fixture
def mock_config():
    """Mock configuration data"""
    return {
        "telegram": {
            "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "chat_id": "123456789"
        },
        "monitoring": {
            "check_interval_seconds": 120,
            "target_account_to_scrape_followers": "testuser",
            "max_followers_to_monitor": 10
        },
        "chrome": {
            "debug_port": 9222,
            "user_data_dir": "C:\\\\temp\\\\chrome-debug-profile"
        }
    }


@pytest.fixture
def temp_config_file(mock_config, tmp_path):
    """Create a temporary config file"""
    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        json.dump(mock_config, f)

    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    yield config_path

    # Restore original directory
    os.chdir(original_dir)


@pytest.fixture
def mock_playwright_page():
    """Mock Playwright page object"""
    page = MagicMock()
    page.url = "https://x.com/home"
    page.title.return_value = "Home / X"
    page.goto = MagicMock()
    page.locator = MagicMock()
    page.evaluate = MagicMock()
    page.content.return_value = "<html><body>Test content</body></html>"
    return page


@pytest.fixture
def mock_playwright_browser():
    """Mock Playwright browser object"""
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    browser.contexts = [context]
    context.pages = [page]

    return browser, page


@pytest.fixture
def mock_playwright():
    """Mock Playwright instance"""
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    playwright.chromium.connect_over_cdp.return_value = browser
    browser.contexts = [context]
    context.pages = [page]

    return playwright


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram Bot"""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=True)
    bot.get_updates = AsyncMock(return_value=[])
    return bot


@pytest.fixture
def sample_accounts_csv(tmp_path):
    """Create a sample accounts CSV file"""
    csv_path = tmp_path / "accounts.csv"
    with open(csv_path, 'w') as f:
        f.write("username,monitored\n")
        f.write("user1,true\n")
        f.write("user2,true\n")
        f.write("user3,false\n")

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    yield csv_path

    os.chdir(original_dir)


@pytest.fixture
def sample_last_posts(tmp_path):
    """Create a sample last_posts.json file"""
    posts = {
        "user1": "1234567890",
        "user2": "0987654321"
    }

    posts_path = tmp_path / "last_posts.json"
    with open(posts_path, 'w') as f:
        json.dump(posts, f)

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    yield posts_path

    os.chdir(original_dir)


@pytest.fixture
def mock_article_element():
    """Mock article element (tweet container)"""
    article = MagicMock()
    time_link = MagicMock()
    time_link.get_attribute.return_value = "/testuser/status/1234567890"

    text_div = MagicMock()
    text_div.inner_text.return_value = "This is a test tweet"

    article.locator.side_effect = lambda selector: (
        time_link if "status" in selector else text_div
    )

    return article
