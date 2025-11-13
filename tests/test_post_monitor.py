"""
Tests for post_monitor.py
"""

import pytest
import json
import csv
import os
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from post_monitor import (
    load_config,
    load_accounts,
    load_last_posts,
    save_last_posts,
    get_chrome_host,
    connect_to_chrome,
    get_latest_post,
    monitor_accounts
)


class TestLoadConfig:
    """Tests for load_config function"""

    def test_load_config_success(self, temp_config_file):
        """Test loading configuration successfully"""
        config = load_config()

        assert config is not None
        assert "telegram" in config
        assert "monitoring" in config
        assert "chrome" in config


class TestLoadAccounts:
    """Tests for load_accounts function"""

    def test_load_accounts_success(self, sample_accounts_csv):
        """Test loading accounts from CSV"""
        accounts = load_accounts()

        assert len(accounts) == 2  # user3 is marked as false
        assert "user1" in accounts
        assert "user2" in accounts
        assert "user3" not in accounts

    def test_load_accounts_file_not_found(self, tmp_path):
        """Test loading accounts when file doesn't exist"""
        os.chdir(tmp_path)

        accounts = load_accounts()

        assert accounts == []

    def test_load_accounts_empty_csv(self, tmp_path):
        """Test loading accounts from empty CSV"""
        os.chdir(tmp_path)

        with open('accounts.csv', 'w') as f:
            f.write("username,monitored\n")

        accounts = load_accounts()

        assert len(accounts) == 0

    def test_load_accounts_all_disabled(self, tmp_path):
        """Test loading accounts when all are disabled"""
        os.chdir(tmp_path)

        with open('accounts.csv', 'w') as f:
            f.write("username,monitored\n")
            f.write("user1,false\n")
            f.write("user2,false\n")

        accounts = load_accounts()

        assert len(accounts) == 0


class TestLoadLastPosts:
    """Tests for load_last_posts and save_last_posts functions"""

    def test_load_last_posts_success(self, sample_last_posts):
        """Test loading last posts from JSON"""
        last_posts = load_last_posts()

        assert last_posts is not None
        assert "user1" in last_posts
        assert last_posts["user1"] == "1234567890"

    def test_load_last_posts_file_not_found(self, tmp_path):
        """Test loading last posts when file doesn't exist"""
        os.chdir(tmp_path)

        last_posts = load_last_posts()

        assert last_posts == {}

    def test_save_last_posts_success(self, tmp_path):
        """Test saving last posts to JSON"""
        os.chdir(tmp_path)

        posts = {
            "user1": "123456",
            "user2": "789012"
        }

        save_last_posts(posts)

        # Verify file was created
        assert os.path.exists("last_posts.json")

        # Read and verify
        with open("last_posts.json", 'r') as f:
            loaded = json.load(f)
            assert loaded == posts

    def test_save_last_posts_overwrite(self, tmp_path):
        """Test overwriting existing last_posts.json"""
        os.chdir(tmp_path)

        # Create initial file
        initial = {"user1": "111"}
        save_last_posts(initial)

        # Overwrite with new data
        new_data = {"user1": "222", "user2": "333"}
        save_last_posts(new_data)

        # Verify overwrite
        loaded = load_last_posts()
        assert loaded == new_data


class TestGetChromeHost:
    """Tests for get_chrome_host function"""

    def test_get_chrome_host_default(self):
        """Test getting Chrome host with default value"""
        with patch('os.path.exists', return_value=False):
            host = get_chrome_host()
            assert host == "127.0.0.1"


class TestConnectToChrome:
    """Tests for connect_to_chrome function"""

    def test_connect_to_chrome_success(self, mock_playwright):
        """Test successful connection to Chrome"""
        with patch('post_monitor.get_chrome_host', return_value="127.0.0.1"):
            browser, page = connect_to_chrome(mock_playwright, debug_port=9222)

            assert browser is not None
            assert page is not None


class TestGetLatestPost:
    """Tests for get_latest_post function"""

    def test_get_latest_post_success(self, mock_playwright_page):
        """Test successfully getting latest post"""
        # Mock article elements
        article = MagicMock()
        time_link = MagicMock()
        time_link.get_attribute.return_value = "/testuser/status/1234567890"
        time_link.first = time_link

        text_div = MagicMock()
        text_div.inner_text.return_value = "Test tweet content"
        text_div.first = text_div

        article.locator.side_effect = lambda selector: (
            time_link if "status" in selector else text_div
        )

        mock_playwright_page.locator.return_value.all.return_value = [article]
        mock_playwright_page.locator.return_value.first = article

        result = get_latest_post(mock_playwright_page, "testuser")

        assert result is not None
        assert result['post_id'] == "1234567890"
        assert result['url'] == "https://x.com/testuser/status/1234567890"
        assert result['text'] == "Test tweet content"

    def test_get_latest_post_no_articles(self, mock_playwright_page):
        """Test getting latest post when no articles found"""
        mock_playwright_page.locator.return_value.all.return_value = []

        result = get_latest_post(mock_playwright_page, "testuser")

        assert result is None

    def test_get_latest_post_account_suspended(self, mock_playwright_page):
        """Test getting latest post from suspended account"""
        mock_playwright_page.content.return_value = "This account has been suspended"

        result = get_latest_post(mock_playwright_page, "testuser")

        assert result is None

    def test_get_latest_post_account_not_found(self, mock_playwright_page):
        """Test getting latest post from non-existent account"""
        mock_playwright_page.content.return_value = "This account doesn't exist"

        result = get_latest_post(mock_playwright_page, "testuser")

        assert result is None

    def test_get_latest_post_network_error(self, mock_playwright_page):
        """Test handling network errors"""
        mock_playwright_page.goto.side_effect = Exception("Network error")

        result = get_latest_post(mock_playwright_page, "testuser")

        assert result is None

    def test_get_latest_post_relative_url(self, mock_playwright_page):
        """Test that relative URLs are converted to absolute"""
        article = MagicMock()
        time_link = MagicMock()
        time_link.get_attribute.return_value = "/testuser/status/123"  # Relative URL
        time_link.first = time_link

        text_div = MagicMock()
        text_div.inner_text.return_value = "Test"
        text_div.first = text_div

        article.locator.side_effect = lambda selector: (
            time_link if "status" in selector else text_div
        )

        mock_playwright_page.locator.return_value.all.return_value = [article]

        result = get_latest_post(mock_playwright_page, "testuser")

        assert result is not None
        assert result['url'].startswith("https://x.com")


class TestMonitorAccounts:
    """Tests for monitor_accounts function"""

    def test_monitor_accounts_first_check(self, mock_playwright_page):
        """Test monitoring accounts on first check (no notifications)"""
        accounts = ["user1", "user2"]
        last_posts = {}

        # Mock get_latest_post
        with patch('post_monitor.get_latest_post') as mock_get_post:
            mock_get_post.side_effect = [
                {'post_id': '111', 'url': 'https://x.com/user1/status/111', 'text': 'Post 1'},
                {'post_id': '222', 'url': 'https://x.com/user2/status/222', 'text': 'Post 2'}
            ]

            # Mock notifier
            mock_notifier = MagicMock()
            mock_notifier.send_new_post_notification_sync.return_value = True

            result = monitor_accounts(mock_playwright_page, accounts, last_posts, mock_notifier)

            # Should record posts but not notify
            assert result['user1'] == '111'
            assert result['user2'] == '222'
            mock_notifier.send_new_post_notification_sync.assert_not_called()

    def test_monitor_accounts_no_new_posts(self, mock_playwright_page):
        """Test monitoring when no new posts"""
        accounts = ["user1"]
        last_posts = {"user1": "111"}

        with patch('post_monitor.get_latest_post') as mock_get_post:
            mock_get_post.return_value = {
                'post_id': '111',
                'url': 'https://x.com/user1/status/111',
                'text': 'Same post'
            }

            mock_notifier = MagicMock()

            result = monitor_accounts(mock_playwright_page, accounts, last_posts, mock_notifier)

            # Should not notify
            assert result['user1'] == '111'
            mock_notifier.send_new_post_notification_sync.assert_not_called()

    def test_monitor_accounts_new_post_detected(self, mock_playwright_page):
        """Test monitoring when new post is detected"""
        accounts = ["user1"]
        last_posts = {"user1": "111"}

        with patch('post_monitor.get_latest_post') as mock_get_post:
            mock_get_post.return_value = {
                'post_id': '222',
                'url': 'https://x.com/user1/status/222',
                'text': 'New post!'
            }

            mock_notifier = MagicMock()
            mock_notifier.send_new_post_notification_sync.return_value = True

            result = monitor_accounts(mock_playwright_page, accounts, last_posts, mock_notifier)

            # Should update and notify
            assert result['user1'] == '222'
            mock_notifier.send_new_post_notification_sync.assert_called_once_with(
                username='user1',
                post_url='https://x.com/user1/status/222',
                post_text='New post!'
            )

    def test_monitor_accounts_multiple_new_posts(self, mock_playwright_page):
        """Test monitoring multiple accounts with new posts"""
        accounts = ["user1", "user2", "user3"]
        last_posts = {"user1": "111", "user2": "222", "user3": "333"}

        with patch('post_monitor.get_latest_post') as mock_get_post:
            mock_get_post.side_effect = [
                {'post_id': '111', 'url': 'https://x.com/user1/status/111', 'text': 'Old'},
                {'post_id': '999', 'url': 'https://x.com/user2/status/999', 'text': 'New!'},
                {'post_id': '888', 'url': 'https://x.com/user3/status/888', 'text': 'Also new!'}
            ]

            mock_notifier = MagicMock()

            result = monitor_accounts(mock_playwright_page, accounts, last_posts, mock_notifier)

            # Should notify for user2 and user3 only
            assert mock_notifier.send_new_post_notification_sync.call_count == 2
            assert result['user1'] == '111'  # Unchanged
            assert result['user2'] == '999'  # Updated
            assert result['user3'] == '888'  # Updated

    def test_monitor_accounts_handles_fetch_errors(self, mock_playwright_page):
        """Test that monitoring continues even if some fetches fail"""
        accounts = ["user1", "user2"]
        last_posts = {}

        with patch('post_monitor.get_latest_post') as mock_get_post:
            mock_get_post.side_effect = [
                None,  # user1 fetch fails
                {'post_id': '222', 'url': 'https://x.com/user2/status/222', 'text': 'Post 2'}
            ]

            mock_notifier = MagicMock()

            result = monitor_accounts(mock_playwright_page, accounts, last_posts, mock_notifier)

            # Should handle failure gracefully
            assert "user1" not in result  # Failed to fetch
            assert result['user2'] == '222'  # Succeeded

    def test_monitor_accounts_empty_list(self, mock_playwright_page):
        """Test monitoring with empty account list"""
        accounts = []
        last_posts = {}

        mock_notifier = MagicMock()

        result = monitor_accounts(mock_playwright_page, accounts, last_posts, mock_notifier)

        assert result == {}
        mock_notifier.send_new_post_notification_sync.assert_not_called()
