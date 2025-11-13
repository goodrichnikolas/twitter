"""
Tests for account_scraper.py
"""

import pytest
import json
import csv
import os
from unittest.mock import Mock, MagicMock, patch
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from account_scraper import (
    load_config,
    get_chrome_host,
    connect_to_chrome,
    scrape_followers,
    save_accounts_to_csv
)


class TestLoadConfig:
    """Tests for load_config function"""

    def test_load_config_success(self, temp_config_file):
        """Test loading configuration successfully"""
        config = load_config()

        assert config is not None
        assert "telegram" in config
        assert "monitoring" in config
        assert config["monitoring"]["target_account_to_scrape_followers"] == "testuser"

    def test_load_config_missing_file(self, tmp_path):
        """Test loading config when file doesn't exist"""
        os.chdir(tmp_path)

        with pytest.raises(FileNotFoundError):
            load_config()


class TestGetChromeHost:
    """Tests for get_chrome_host function"""

    def test_get_chrome_host_default(self):
        """Test getting Chrome host with default value"""
        with patch('os.path.exists', return_value=False):
            host = get_chrome_host()
            assert host == "127.0.0.1"

    def test_get_chrome_host_wsl2(self, tmp_path):
        """Test getting Chrome host in WSL2 environment"""
        # Create a mock resolv.conf
        resolv_conf = tmp_path / "resolv.conf"
        with open(resolv_conf, 'w') as f:
            f.write("# This is a comment\n")
            f.write("nameserver 192.168.1.1\n")
            f.write("nameserver 8.8.8.8\n")

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', return_value=open(resolv_conf, 'r')):
                host = get_chrome_host()
                assert host == "192.168.1.1"


class TestConnectToChrome:
    """Tests for connect_to_chrome function"""

    def test_connect_to_chrome_success(self, mock_playwright):
        """Test successful connection to Chrome"""
        with patch('account_scraper.get_chrome_host', return_value="127.0.0.1"):
            browser, page = connect_to_chrome(mock_playwright, debug_port=9222)

            assert browser is not None
            assert page is not None
            mock_playwright.chromium.connect_over_cdp.assert_called_once()

    def test_connect_to_chrome_custom_port(self, mock_playwright):
        """Test connection with custom port"""
        with patch('account_scraper.get_chrome_host', return_value="127.0.0.1"):
            browser, page = connect_to_chrome(mock_playwright, debug_port=9999)

            call_args = mock_playwright.chromium.connect_over_cdp.call_args
            assert "9999" in call_args[0][0]

    def test_connect_to_chrome_no_existing_page(self, mock_playwright):
        """Test connection when no pages exist"""
        # Mock browser with empty pages
        browser = MagicMock()
        context = MagicMock()
        context.pages = []
        new_page = MagicMock()
        context.new_page.return_value = new_page

        browser.contexts = [context]
        mock_playwright.chromium.connect_over_cdp.return_value = browser

        with patch('account_scraper.get_chrome_host', return_value="127.0.0.1"):
            _, page = connect_to_chrome(mock_playwright)

            assert page == new_page
            context.new_page.assert_called_once()


class TestScrapeFollowers:
    """Tests for scrape_followers function"""

    def test_scrape_followers_success(self, mock_playwright_page):
        """Test successful follower scraping"""
        # Mock user links
        link1 = MagicMock()
        link1.get_attribute.return_value = "/user1"

        link2 = MagicMock()
        link2.get_attribute.return_value = "/user2"

        link3 = MagicMock()
        link3.get_attribute.return_value = "/user3"

        mock_playwright_page.locator.return_value.all.return_value = [link1, link2, link3]

        followers = scrape_followers(mock_playwright_page, "testuser", max_followers=3)

        assert len(followers) <= 3
        mock_playwright_page.goto.assert_called_once()

    def test_scrape_followers_not_logged_in(self, mock_playwright_page):
        """Test scraping when not logged in"""
        mock_playwright_page.url = "https://x.com/login"

        followers = scrape_followers(mock_playwright_page, "testuser", max_followers=10)

        assert followers == []

    def test_scrape_followers_filters_invalid_usernames(self, mock_playwright_page):
        """Test that invalid usernames are filtered out"""
        # Mock links with various types
        link1 = MagicMock()
        link1.get_attribute.return_value = "/validuser"

        link2 = MagicMock()
        link2.get_attribute.return_value = "/user/status/123"  # Should be filtered

        link3 = MagicMock()
        link3.get_attribute.return_value = "/i/flow/signup"  # Should be filtered

        link4 = MagicMock()
        link4.get_attribute.return_value = "/search?q=test"  # Should be filtered

        mock_playwright_page.locator.return_value.all.return_value = [link1, link2, link3, link4]

        followers = scrape_followers(mock_playwright_page, "testuser", max_followers=10)

        # Only validuser should be included
        assert "validuser" in followers
        assert len([f for f in followers if "status" in f]) == 0
        assert len([f for f in followers if "/i/" in f]) == 0

    def test_scrape_followers_stops_at_max(self, mock_playwright_page):
        """Test that scraping stops at max_followers"""
        # Create many mock links
        links = []
        for i in range(50):
            link = MagicMock()
            link.get_attribute.return_value = f"/user{i}"
            links.append(link)

        mock_playwright_page.locator.return_value.all.return_value = links

        followers = scrape_followers(mock_playwright_page, "testuser", max_followers=10)

        assert len(followers) <= 10

    def test_scrape_followers_handles_exceptions(self, mock_playwright_page):
        """Test that exceptions during scraping are handled"""
        # Mock link that raises exception
        link = MagicMock()
        link.get_attribute.side_effect = Exception("Network error")

        mock_playwright_page.locator.return_value.all.return_value = [link]

        # Should not raise exception
        followers = scrape_followers(mock_playwright_page, "testuser", max_followers=10)

        assert isinstance(followers, list)


class TestSaveAccountsToCSV:
    """Tests for save_accounts_to_csv function"""

    def test_save_accounts_to_csv_success(self, tmp_path):
        """Test saving accounts to CSV successfully"""
        os.chdir(tmp_path)

        accounts = ["user1", "user2", "user3"]
        save_accounts_to_csv(accounts)

        # Check file was created
        assert os.path.exists("accounts.csv")

        # Read and verify contents
        with open("accounts.csv", 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 3
            assert rows[0]['username'] == "user1"
            assert rows[0]['monitored'] == "true"

    def test_save_accounts_to_csv_custom_filename(self, tmp_path):
        """Test saving accounts with custom filename"""
        os.chdir(tmp_path)

        accounts = ["user1", "user2"]
        filename = "custom_accounts.csv"
        save_accounts_to_csv(accounts, filename=filename)

        assert os.path.exists(filename)

    def test_save_accounts_to_csv_empty_list(self, tmp_path):
        """Test saving empty accounts list"""
        os.chdir(tmp_path)

        accounts = []
        save_accounts_to_csv(accounts)

        with open("accounts.csv", 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 0

    def test_save_accounts_to_csv_unicode(self, tmp_path):
        """Test saving accounts with unicode characters"""
        os.chdir(tmp_path)

        accounts = ["user_日本", "user_中文", "user_עברית"]
        save_accounts_to_csv(accounts)

        with open("accounts.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 3
            assert "日本" in rows[0]['username']


class TestMainFunction:
    """Tests for main function behavior"""

    def test_main_missing_config(self, tmp_path):
        """Test main function with missing config"""
        from account_scraper import main

        os.chdir(tmp_path)

        # Should handle missing config gracefully
        # We can't easily test the full main() due to input() calls,
        # but we can test that it handles missing config
        with patch('account_scraper.load_config', side_effect=FileNotFoundError):
            main()  # Should not crash

    def test_main_unconfigured_target(self, temp_config_file):
        """Test main function with unconfigured target account"""
        from account_scraper import main

        config = load_config()
        config['monitoring']['target_account_to_scrape_followers'] = "ACCOUNT_USERNAME_HERE"

        with open('config.json', 'w') as f:
            json.dump(config, f)

        # Should exit gracefully when target is not configured
        main()  # Should not crash
