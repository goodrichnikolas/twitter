#!/usr/bin/env python3
"""
Telegram Notifier - Sends notifications via Telegram bot
"""

import json
import asyncio
import csv
from pathlib import Path
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
        self.last_notified_account = None  # Track last account we notified about
        self.last_update_id = None  # Track last processed Telegram update

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
        # Track this as the last notified account
        self.last_notified_account = username

        message = f"🚨 <b>New post from @{username}</b>\n\n"

        if post_text:
            # Truncate if too long
            preview = post_text[:200] + "..." if len(post_text) > 200 else post_text
            # Escape HTML special characters
            preview = preview.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            message += f"<i>{preview}</i>\n\n"

        message += f"<a href='{post_url}'>View Post</a>\n\n"
        message += f"<i>Reply with 'x' or 'X' to remove @{username} from monitoring</i>"

        return await self.send_message(message)

    async def get_updates(self):
        """
        Get updates (messages) from Telegram.

        Returns:
            List of updates
        """
        try:
            updates = await self.bot.get_updates(
                offset=self.last_update_id + 1 if self.last_update_id else None,
                timeout=1
            )

            if updates:
                # Update the last_update_id to mark these as processed
                self.last_update_id = updates[-1].update_id

            return updates
        except TelegramError as e:
            print(f"Failed to get Telegram updates: {e}")
            return []

    async def check_for_commands(self):
        """
        Check for commands from Telegram.

        Returns:
            Dictionary with command results or None
            {
                'command': 'x',
                'account_to_remove': 'username'
            }
        """
        updates = await self.get_updates()

        for update in updates:
            if update.message and update.message.text:
                text = update.message.text.strip().lower()

                # Check if message is from the configured chat
                if str(update.message.chat_id) == str(self.chat_id):
                    # Handle 'x' command to remove last notified account
                    if text == 'x':
                        if self.last_notified_account:
                            return {
                                'command': 'x',
                                'account_to_remove': self.last_notified_account
                            }
                        else:
                            await self.send_message("⚠️ No recent notification to remove")

                    # Handle 'x @username' command to remove specific account
                    elif text.startswith('x @'):
                        username = text.split('@', 1)[1].strip()
                        return {
                            'command': 'x',
                            'account_to_remove': username
                        }

        return None

    def remove_account_from_monitoring(self, username):
        """
        Remove account from accounts.csv and add to small_accounts.csv.

        Args:
            username: Username to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load current accounts
            accounts_path = Path('accounts.csv')
            accounts = set()

            if accounts_path.exists():
                with open(accounts_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and not row[0].startswith('#') and row[0] != 'username':
                            acc = row[0].strip().lstrip('@')
                            accounts.add(acc)

            # Remove the account
            username = username.lstrip('@')
            if username not in accounts:
                return False

            accounts.remove(username)

            # Save updated accounts.csv
            with open(accounts_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['username'])
                for acc in sorted(accounts):
                    writer.writerow([acc])

            # Add to small_accounts.csv
            small_accounts_path = Path('small_accounts.csv')
            file_exists = small_accounts_path.exists()

            with open(small_accounts_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['username'])
                writer.writerow([username])

            return True

        except Exception as e:
            print(f"Error removing account {username}: {e}")
            return False

    def send_message_sync(self, message, parse_mode='HTML'):
        """Synchronous wrapper for send_message"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_message(message, parse_mode))

    def send_new_post_notification_sync(self, username, post_url, post_text=None):
        """Synchronous wrapper for send_new_post_notification"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_new_post_notification(username, post_url, post_text))

    def check_for_commands_sync(self):
        """Synchronous wrapper for check_for_commands"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.check_for_commands())

    def process_commands(self):
        """
        Check for and process Telegram commands.

        Returns:
            Dictionary with results or None
        """
        command = self.check_for_commands_sync()

        if command and command['command'] == 'x':
            username = command['account_to_remove']

            # Remove account
            if self.remove_account_from_monitoring(username):
                self.send_message_sync(
                    f"✅ Removed @{username} from monitoring\n\n"
                    f"Added to small_accounts.csv"
                )
                # Clear last notified account
                self.last_notified_account = None
                return {
                    'removed': username,
                    'success': True
                }
            else:
                self.send_message_sync(
                    f"❌ Failed to remove @{username}\n\n"
                    f"Account not found in accounts.csv"
                )
                return {
                    'removed': username,
                    'success': False
                }

        return None


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
