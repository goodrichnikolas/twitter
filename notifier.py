#!/usr/bin/env python3
"""
Telegram Notifier - Sends notifications via Telegram bot
"""

import json
import asyncio
from telegram import Bot
from telegram.error import TelegramError


class TelegramNotifier:
    """Handles sending notifications via Telegram"""

    def __init__(self, bot_token, chat_id):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Your Telegram chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)

    async def send_message(self, message, parse_mode='HTML'):
        """
        Send a message via Telegram.

        Args:
            message: Message text to send
            parse_mode: 'HTML' or 'Markdown'

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=False
            )
            return True
        except TelegramError as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    async def send_new_post_notification(self, username, post_url, post_text=None):
        """
        Send notification about a new post.

        Args:
            username: Twitter username who posted
            post_url: URL to the post
            post_text: Preview of post text (optional)
        """
        message = f"🚨 <b>New post from @{username}</b>\n\n"

        if post_text:
            # Truncate if too long
            preview = post_text[:200] + "..." if len(post_text) > 200 else post_text
            # Escape HTML special characters
            preview = preview.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            message += f"<i>{preview}</i>\n\n"

        message += f"<a href='{post_url}'>View Post</a>"

        return await self.send_message(message)

    def send_message_sync(self, message, parse_mode='HTML'):
        """Synchronous wrapper for send_message"""
        return asyncio.run(self.send_message(message, parse_mode))

    def send_new_post_notification_sync(self, username, post_url, post_text=None):
        """Synchronous wrapper for send_new_post_notification"""
        return asyncio.run(self.send_new_post_notification(username, post_url, post_text))


def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        return json.load(f)


async def test_notification():
    """Test the Telegram notification system"""
    config = load_config()

    bot_token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']

    if bot_token == "YOUR_BOT_TOKEN_HERE" or chat_id == "YOUR_CHAT_ID_HERE":
        print("ERROR: Please configure your Telegram bot token and chat ID in config.json")
        print()
        print("To set up:")
        print("1. Talk to @BotFather on Telegram to create a bot")
        print("2. Copy the bot token to config.json")
        print("3. Message your bot, then run this script with --get-chat-id")
        return

    notifier = TelegramNotifier(bot_token, chat_id)

    print("Sending test notification...")
    success = await notifier.send_message("✅ <b>Notification system working!</b>\n\nYou'll receive alerts here when monitored accounts post.")

    if success:
        print("✓ Test notification sent successfully!")
        print("Check your Telegram to confirm you received it.")
    else:
        print("✗ Failed to send notification. Check your bot token and chat ID.")


async def get_chat_id():
    """Helper to get your Telegram chat ID"""
    config = load_config()
    bot_token = config['telegram']['bot_token']

    if bot_token == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Please set your bot token in config.json first")
        return

    bot = Bot(token=bot_token)

    print("Fetching recent messages...")
    print("Make sure you've sent a message to your bot first!")
    print()

    try:
        updates = await bot.get_updates()
        if updates:
            for update in updates[-5:]:  # Show last 5
                if update.message:
                    chat_id = update.message.chat.id
                    username = update.message.from_user.username or "N/A"
                    print(f"Chat ID: {chat_id} (from @{username})")
            print()
            print("Copy one of these Chat IDs to config.json")
        else:
            print("No messages found. Please send a message to your bot first.")
    except TelegramError as e:
        print(f"Error: {e}")


def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--get-chat-id':
        asyncio.run(get_chat_id())
    else:
        asyncio.run(test_notification())


if __name__ == "__main__":
    main()
