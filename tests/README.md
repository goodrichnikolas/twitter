# Test Suite

This directory contains comprehensive tests for the Twitter/X Early Response System.

## Running Tests

### Run all tests
```bash
pytest
```

### Run tests with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_notifier.py
```

### Run specific test class
```bash
pytest tests/test_notifier.py::TestTelegramNotifier
```

### Run specific test
```bash
pytest tests/test_notifier.py::TestTelegramNotifier::test_send_message_success
```

### Run tests matching a pattern
```bash
pytest -k "test_load"
```

### Run with verbose output
```bash
pytest -v
```

### Run async tests only
```bash
pytest -m asyncio
```

### Skip async tests
```bash
pytest -m "not asyncio"
```

## Test Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_notifier.py` - Tests for Telegram notification system
- `test_account_scraper.py` - Tests for account scraping functionality
- `test_post_monitor.py` - Tests for post monitoring service
- `test_chrome_test.py` - Tests for Chrome connection utilities

## Test Coverage

After running tests with coverage, open `htmlcov/index.html` to view detailed coverage report:

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html  # or xdg-open on Linux
```

## Fixtures

Common fixtures available in all tests (from `conftest.py`):

- `mock_config` - Mock configuration dictionary
- `temp_config_file` - Temporary config.json file
- `mock_playwright_page` - Mock Playwright page object
- `mock_playwright_browser` - Mock Playwright browser and page
- `mock_playwright` - Mock Playwright instance
- `mock_telegram_bot` - Mock Telegram bot
- `sample_accounts_csv` - Sample accounts.csv file
- `sample_last_posts` - Sample last_posts.json file
- `mock_article_element` - Mock tweet article element

## Writing New Tests

### Example test structure:

```python
import pytest
from unittest.mock import Mock, patch

class TestMyFeature:
    """Tests for my feature"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        result = my_function()
        assert result == expected_value

    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            my_function(invalid_input)

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function"""
        result = await my_async_function()
        assert result is True
```

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=. --cov-report=xml
```

## Troubleshooting

**Import errors**: Make sure you're running pytest from the project root directory.

**Async test failures**: Ensure `pytest-asyncio` is installed and `asyncio_mode = auto` is set in `pytest.ini`.

**Coverage not working**: Ensure `pytest-cov` is installed and `.coveragerc` is in the project root.
