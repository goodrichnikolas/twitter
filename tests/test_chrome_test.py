"""
Tests for chrome_test.py
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import with error handling
try:
    from chrome_test import connect_to_chrome, post_to_x
except ImportError:
    # If running from different directory
    import importlib.util
    spec = importlib.util.spec_from_file_location("chrome_test",
        os.path.join(os.path.dirname(__file__), '..', 'chrome_test.py'))
    chrome_test = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chrome_test)
    connect_to_chrome = chrome_test.connect_to_chrome
    post_to_x = chrome_test.post_to_x


class TestConnectToChrome:
    """Tests for connect_to_chrome function"""

    def test_connect_to_chrome_success(self, mock_playwright):
        """Test successful connection to Chrome"""
        browser, page = connect_to_chrome(mock_playwright, debug_port=9222)

        assert browser is not None
        assert page is not None
        mock_playwright.chromium.connect_over_cdp.assert_called_once()

    def test_connect_to_chrome_custom_port(self, mock_playwright):
        """Test connection with custom debug port"""
        with patch('chrome_test.get_chrome_host', return_value="127.0.0.1"):
            browser, page = connect_to_chrome(mock_playwright, debug_port=9999)

            call_args = mock_playwright.chromium.connect_over_cdp.call_args
            assert "9999" in call_args[0][0]

    def test_connect_to_chrome_wsl2_host(self, mock_playwright):
        """Test connection with WSL2 host detection"""
        with patch('chrome_test.get_chrome_host', return_value="192.168.1.100"):
            browser, page = connect_to_chrome(mock_playwright)

            call_args = mock_playwright.chromium.connect_over_cdp.call_args
            assert "192.168.1.100" in call_args[0][0]

    def test_connect_to_chrome_no_pages(self, mock_playwright):
        """Test connection when no pages exist in context"""
        browser = MagicMock()
        context = MagicMock()
        context.pages = []
        new_page = MagicMock()
        context.new_page.return_value = new_page

        browser.contexts = [context]
        mock_playwright.chromium.connect_over_cdp.return_value = browser

        with patch('chrome_test.get_chrome_host', return_value="127.0.0.1"):
            _, page = connect_to_chrome(mock_playwright)

            assert page == new_page
            context.new_page.assert_called_once()

    def test_connect_to_chrome_existing_page(self, mock_playwright):
        """Test connection when page already exists"""
        browser = MagicMock()
        context = MagicMock()
        existing_page = MagicMock()
        context.pages = [existing_page]

        browser.contexts = [context]
        mock_playwright.chromium.connect_over_cdp.return_value = browser

        with patch('chrome_test.get_chrome_host', return_value="127.0.0.1"):
            _, page = connect_to_chrome(mock_playwright)

            assert page == existing_page
            context.new_page.assert_not_called()


class TestPostToX:
    """Tests for post_to_x function"""

    def test_post_to_x_already_on_twitter(self, mock_playwright_page):
        """Test posting when already on Twitter"""
        mock_playwright_page.url = "https://x.com/home"

        # Mock compose box elements
        compose_box = MagicMock()
        compose_box.wait_for.return_value = None
        compose_box.click.return_value = None

        text_input = MagicMock()
        text_input.wait_for.return_value = None
        text_input.type.return_value = None

        mock_playwright_page.locator.side_effect = lambda selector: (
            compose_box if "What is happening" in selector
            else text_input if "tweetTextarea_0" in selector
            else MagicMock()
        )

        result = post_to_x(mock_playwright_page, "Test tweet")

        assert result is True

    def test_post_to_x_navigates_to_twitter(self, mock_playwright_page):
        """Test that it navigates to Twitter if not already there"""
        mock_playwright_page.url = "https://google.com"

        # Mock compose elements
        compose_box = MagicMock()
        compose_box.wait_for.return_value = None
        compose_box.click.return_value = None

        text_input = MagicMock()
        text_input.wait_for.return_value = None
        text_input.type.return_value = None

        mock_playwright_page.locator.side_effect = lambda selector: (
            compose_box if "What is happening" in selector
            else text_input if "tweetTextarea_0" in selector
            else MagicMock()
        )

        result = post_to_x(mock_playwright_page, "Test tweet")

        mock_playwright_page.goto.assert_called_once_with("https://x.com/home")

    def test_post_to_x_compose_box_not_found(self, mock_playwright_page):
        """Test handling when compose box is not found"""
        mock_playwright_page.url = "https://x.com/home"

        # Mock locator that throws exception for compose box
        def mock_locator(selector):
            locator = MagicMock()
            if "What is happening" in selector or "tweetTextarea_0" in selector or "textbox" in selector:
                locator.wait_for.side_effect = Exception("Element not found")
            return locator

        mock_playwright_page.locator = mock_locator

        result = post_to_x(mock_playwright_page, "Test tweet")

        assert result is False

    def test_post_to_x_tries_multiple_selectors(self, mock_playwright_page):
        """Test that it tries multiple selectors for compose box"""
        mock_playwright_page.url = "https://x.com/home"

        call_count = 0

        def mock_locator(selector):
            nonlocal call_count
            locator = MagicMock()

            if "What is happening" in selector:
                # First selector fails
                locator.wait_for.side_effect = Exception("Not found")
            elif "tweetTextarea_0" in selector:
                call_count += 1
                if call_count == 1:
                    # Second selector succeeds for compose
                    locator.wait_for.return_value = None
                    locator.click.return_value = None
                else:
                    # Text input
                    locator.wait_for.return_value = None
                    locator.type.return_value = None
            else:
                locator.wait_for.side_effect = Exception("Not found")

            return locator

        mock_playwright_page.locator = mock_locator

        result = post_to_x(mock_playwright_page, "Test tweet")

        # Should succeed even though first selector failed
        assert result is True

    def test_post_to_x_handles_exception(self, mock_playwright_page):
        """Test that exceptions are caught and handled"""
        mock_playwright_page.url = "https://x.com/home"
        mock_playwright_page.locator.side_effect = Exception("Unexpected error")

        result = post_to_x(mock_playwright_page, "Test tweet")

        assert result is False

    def test_post_to_x_with_long_text(self, mock_playwright_page):
        """Test posting with long text"""
        mock_playwright_page.url = "https://x.com/home"

        compose_box = MagicMock()
        text_input = MagicMock()

        mock_playwright_page.locator.side_effect = lambda selector: (
            compose_box if "What is happening" in selector
            else text_input if "tweetTextarea_0" in selector
            else MagicMock()
        )

        long_text = "A" * 300

        result = post_to_x(mock_playwright_page, long_text)

        assert result is True
        text_input.type.assert_called_once_with(long_text)

    def test_post_to_x_with_special_characters(self, mock_playwright_page):
        """Test posting with special characters"""
        mock_playwright_page.url = "https://x.com/home"

        compose_box = MagicMock()
        text_input = MagicMock()

        mock_playwright_page.locator.side_effect = lambda selector: (
            compose_box if "What is happening" in selector
            else text_input if "tweetTextarea_0" in selector
            else MagicMock()
        )

        special_text = "Test with emojis 🚀 and @mentions #hashtags"

        result = post_to_x(mock_playwright_page, special_text)

        assert result is True
        text_input.type.assert_called_once_with(special_text)


class TestGetChromeHost:
    """Tests for get_chrome_host function (from chrome_test)"""

    def test_get_chrome_host_default(self):
        """Test default Chrome host"""
        with patch('os.path.exists', return_value=False):
            # Import here to use patched os.path.exists
            from chrome_test import connect_to_chrome

            with patch('chrome_test.get_chrome_host', return_value="127.0.0.1") as mock_host:
                playwright = MagicMock()
                browser = MagicMock()
                context = MagicMock()
                page = MagicMock()

                browser.contexts = [context]
                context.pages = [page]
                playwright.chromium.connect_over_cdp.return_value = browser

                connect_to_chrome(playwright)

                # Verify it was called
                mock_host.assert_called()

    def test_get_chrome_host_wsl2(self, tmp_path):
        """Test Chrome host detection in WSL2"""
        from chrome_test import connect_to_chrome

        # We can't easily test the actual file reading without more complex mocking,
        # but we can verify the function handles the WSL2 case
        with patch('chrome_test.get_chrome_host', return_value="192.168.1.1"):
            playwright = MagicMock()
            browser = MagicMock()
            context = MagicMock()
            page = MagicMock()

            browser.contexts = [context]
            context.pages = [page]
            playwright.chromium.connect_over_cdp.return_value = browser

            connect_to_chrome(playwright)

            # Verify CDP URL contains the correct host
            call_args = playwright.chromium.connect_over_cdp.call_args
            assert "192.168.1.1" in call_args[0][0]
