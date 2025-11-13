"""
Tests for notifier.py
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram.error import TelegramError
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notifier import TelegramNotifier, load_config


class TestTelegramNotifier:
    """Tests for TelegramNotifier class"""

    def test_init(self):
        """Test TelegramNotifier initialization"""
        bot_token = "test_token"
        chat_id = "12345"

        notifier = TelegramNotifier(bot_token, chat_id)

        assert notifier.bot_token == bot_token
        assert notifier.chat_id == chat_id
        assert notifier.bot is not None

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending"""
        notifier = TelegramNotifier("test_token", "12345")

        # Mock the bot's send_message
        notifier.bot.send_message = AsyncMock(return_value=True)

        result = await notifier.send_message("Test message")

        assert result is True
        notifier.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """Test message sending failure"""
        notifier = TelegramNotifier("test_token", "12345")

        # Mock the bot to raise an error
        notifier.bot.send_message = AsyncMock(side_effect=TelegramError("Network error"))

        result = await notifier.send_message("Test message")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_new_post_notification_with_text(self):
        """Test sending new post notification with text preview"""
        notifier = TelegramNotifier("test_token", "12345")
        notifier.bot.send_message = AsyncMock(return_value=True)

        result = await notifier.send_new_post_notification(
            username="testuser",
            post_url="https://x.com/testuser/status/123",
            post_text="This is a test tweet"
        )

        assert result is True
        notifier.bot.send_message.assert_called_once()

        # Check that the message contains expected content
        call_args = notifier.bot.send_message.call_args
        message = call_args.kwargs['text']
        assert "testuser" in message
        assert "This is a test tweet" in message
        assert "https://x.com/testuser/status/123" in message

    @pytest.mark.asyncio
    async def test_send_new_post_notification_without_text(self):
        """Test sending new post notification without text preview"""
        notifier = TelegramNotifier("test_token", "12345")
        notifier.bot.send_message = AsyncMock(return_value=True)

        result = await notifier.send_new_post_notification(
            username="testuser",
            post_url="https://x.com/testuser/status/123"
        )

        assert result is True
        notifier.bot.send_message.assert_called_once()

        call_args = notifier.bot.send_message.call_args
        message = call_args.kwargs['text']
        assert "testuser" in message
        assert "https://x.com/testuser/status/123" in message

    @pytest.mark.asyncio
    async def test_send_new_post_notification_long_text(self):
        """Test sending notification with long text that gets truncated"""
        notifier = TelegramNotifier("test_token", "12345")
        notifier.bot.send_message = AsyncMock(return_value=True)

        long_text = "A" * 300

        result = await notifier.send_new_post_notification(
            username="testuser",
            post_url="https://x.com/testuser/status/123",
            post_text=long_text
        )

        assert result is True

        call_args = notifier.bot.send_message.call_args
        message = call_args.kwargs['text']
        assert "..." in message  # Should be truncated

    @pytest.mark.asyncio
    async def test_send_message_html_escaping(self):
        """Test that HTML special characters are escaped"""
        notifier = TelegramNotifier("test_token", "12345")
        notifier.bot.send_message = AsyncMock(return_value=True)

        result = await notifier.send_new_post_notification(
            username="testuser",
            post_url="https://x.com/testuser/status/123",
            post_text="Test <tag> & special > characters"
        )

        assert result is True

        call_args = notifier.bot.send_message.call_args
        message = call_args.kwargs['text']
        assert "&lt;tag&gt;" in message
        assert "&amp;" in message

    def test_send_message_sync(self):
        """Test synchronous wrapper for send_message"""
        notifier = TelegramNotifier("test_token", "12345")

        with patch.object(notifier, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = notifier.send_message_sync("Test message")

            assert result is True

    def test_send_new_post_notification_sync(self):
        """Test synchronous wrapper for send_new_post_notification"""
        notifier = TelegramNotifier("test_token", "12345")

        with patch.object(notifier, 'send_new_post_notification', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = notifier.send_new_post_notification_sync(
                username="testuser",
                post_url="https://x.com/test/123"
            )

            assert result is True


class TestLoadConfig:
    """Tests for load_config function"""

    def test_load_config_success(self, temp_config_file):
        """Test loading config successfully"""
        config = load_config()

        assert config is not None
        assert "telegram" in config
        assert "monitoring" in config
        assert "chrome" in config

    def test_load_config_file_not_found(self, tmp_path):
        """Test loading config when file doesn't exist"""
        os.chdir(tmp_path)

        with pytest.raises(FileNotFoundError):
            load_config()


@pytest.mark.asyncio
async def test_get_chat_id(tmp_path, mock_config):
    """Test get_chat_id function"""
    from notifier import get_chat_id

    # Create config file
    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        json.dump(mock_config, f)

    os.chdir(tmp_path)

    # Mock the Bot and its get_updates method
    with patch('notifier.Bot') as mock_bot_class:
        mock_bot = AsyncMock()
        mock_update = Mock()
        mock_update.message.chat.id = 123456789
        mock_update.message.from_user.username = "testuser"
        mock_bot.get_updates.return_value = [mock_update]
        mock_bot_class.return_value = mock_bot

        # Should not raise an error
        await get_chat_id()


@pytest.mark.asyncio
async def test_test_notification(tmp_path, mock_config):
    """Test test_notification function"""
    from notifier import test_notification

    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        json.dump(mock_config, f)

    os.chdir(tmp_path)

    with patch('notifier.TelegramNotifier') as mock_notifier_class:
        mock_notifier = Mock()
        mock_notifier.send_message = AsyncMock(return_value=True)
        mock_notifier_class.return_value = mock_notifier

        await test_notification()

        mock_notifier.send_message.assert_called_once()
