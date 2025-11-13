#!/usr/bin/env python3
"""
Twitter Monitor Service using TwitterAPI.io

Workflow:
1. Load accounts from accounts.csv
2. Check each account one by one
3. Wait 60 seconds between each check
4. If tweet is within last 10 minutes → Alert via Telegram
5. If not → Print "None found" and move to next
"""

import csv
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List

from .client import TwitterAPIClient
from notifier import TelegramNotifier
from monitor_state import MonitorState


def load_accounts(csv_path: str = 'accounts.csv') -> List[str]:
    """
    Load accounts from CSV file.

    Args:
        csv_path: Path to accounts CSV file

    Returns:
        List of usernames
    """
    accounts = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    username = row[0].strip()
                    # Skip header and empty lines
                    if username and username != 'username':
                        username = username.lstrip('@')
                        accounts.append(username)

        return accounts

    except FileNotFoundError:
        print(f"ERROR: {csv_path} not found")
        print("Run account_scraper.py to generate accounts.csv")
        return []


def load_config(config_path: str = 'config.json') -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def monitor_accounts(
    api_client: TwitterAPIClient,
    notifier: TelegramNotifier,
    accounts: List[str],
    recent_minutes: int = 10,
    check_interval: int = 60,
    state: MonitorState = None
):
    """
    Monitor accounts for recent posts.

    Args:
        api_client: TwitterAPI.io client
        notifier: Telegram notifier
        accounts: List of usernames to monitor
        recent_minutes: Threshold for recent posts (default: 10)
        check_interval: Seconds to wait between checks (default: 60)
        state: MonitorState for tracking notifications and cooldowns
    """
    # Initialize state if not provided
    if state is None:
        state = MonitorState()

    # Filter out accounts in cooldown
    accounts_to_check = []
    accounts_in_cooldown = []

    for username in accounts:
        if state.is_in_cooldown(username, cooldown_minutes=recent_minutes):
            remaining = state.get_cooldown_remaining(username, cooldown_minutes=recent_minutes)
            accounts_in_cooldown.append((username, remaining))
        else:
            accounts_to_check.append(username)

    total_accounts = len(accounts_to_check)
    estimated_time = (total_accounts * check_interval) / 60  # in minutes

    print(f"\n{'='*70}")
    print(f"Starting monitoring cycle")
    print(f"Accounts to check: {total_accounts}")
    if accounts_in_cooldown:
        print(f"Accounts in cooldown: {len(accounts_in_cooldown)}")
    print(f"Check interval: {check_interval} seconds")
    print(f"Recent threshold: {recent_minutes} minutes")
    print(f"Estimated cycle time: {estimated_time:.1f} minutes ({estimated_time/60:.1f} hours)")
    print(f"{'='*70}\n")

    for i, username in enumerate(accounts_to_check, 1):
        # Check for Telegram commands before each account check
        try:
            command_result = notifier.process_commands()
            if command_result and command_result.get('success'):
                removed = command_result['removed']
                print(f"  ℹ️  Removed @{removed} from monitoring via Telegram command")
                # If we removed the current account, skip it
                if removed == username:
                    print(f"  Skipping @{username} (just removed)\n")
                    continue
        except Exception as e:
            pass  # Silently ignore command check errors

        cycle_start = time.time()

        print(f"[{i}/{total_accounts}] Checking @{username}...")

        notification_sent = False

        try:
            # Check for recent post
            recent_post = api_client.is_recent_post(username, minutes_threshold=recent_minutes)

            if recent_post:
                tweet_id = recent_post.get('tweet_id')

                # Check if we've already notified about this tweet
                if tweet_id and state.has_been_notified(tweet_id):
                    print(f"  ℹ️  Recent post found but already notified (skipping)")
                    print(f"  Tweet ID: {tweet_id}")
                else:
                    # Recent post found and not yet notified
                    minutes_ago = recent_post['minutes_ago']
                    print(f"  🚨 RECENT POST! Posted {minutes_ago:.1f} minutes ago")
                    print(f"  URL: {recent_post['url']}")
                    if tweet_id:
                        print(f"  Tweet ID: {tweet_id}")

                    # Send Telegram notification
                    notifier.send_new_post_notification_sync(
                        username=username,
                        post_url=recent_post['url'],
                        post_text=recent_post['text'][:200]  # Limit text length
                    )

                    print(f"  ✓ Telegram notification sent")
                    notification_sent = True

                    # Mark as notified and set cooldown
                    if tweet_id:
                        state.mark_as_notified(tweet_id, username)
                        print(f"  ✓ Cooldown activated ({recent_minutes} minutes)")

            else:
                # No recent post
                print(f"  None found in the past {recent_minutes} minutes")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Only wait if we sent a notification (unless it's the last account)
        if i < total_accounts:
            if notification_sent:
                # Wait after sending notification
                elapsed = time.time() - cycle_start
                sleep_time = max(0, check_interval - elapsed)

                if sleep_time > 0:
                    print(f"  Waiting {sleep_time:.0f} seconds before next check...\n")
                    time.sleep(sleep_time)
                else:
                    print()  # Just add newline if no sleep needed
            else:
                # No notification sent - continue immediately
                print()

    print(f"{'='*70}")
    print(f"Cycle complete! Checked {total_accounts} accounts")
    print(f"{'='*70}\n")


def run_continuous_monitoring(
    api_client: TwitterAPIClient,
    notifier: TelegramNotifier,
    accounts: List[str],
    recent_minutes: int = 10,
    check_interval: int = 60
):
    """
    Run continuous monitoring in an infinite loop.

    Args:
        api_client: TwitterAPI.io client
        notifier: Telegram notifier
        accounts: List of usernames to monitor
        recent_minutes: Threshold for recent posts (default: 10)
        check_interval: Seconds to wait between checks (default: 60)
    """
    # Initialize state manager
    state = MonitorState()
    stats = state.get_stats()

    cycle_number = 0

    print(f"\n{'='*70}")
    print(f"Twitter Monitor - Continuous Mode")
    print(f"{'='*70}")
    print(f"Monitoring {len(accounts)} accounts")
    print(f"Check interval: {check_interval} seconds between accounts")
    print(f"Recent threshold: {recent_minutes} minutes")
    print(f"Cooldown period: {recent_minutes} minutes after notification")
    print(f"\nState:")
    print(f"  Tweets tracked: {stats['total_tweets_tracked']}")
    print(f"  Accounts in cooldown: {stats['accounts_in_cooldown']}")
    print(f"\nPress Ctrl+C to stop")
    print(f"{'='*70}\n")

    # Send startup notification
    notifier.send_message_sync(
        "🤖 <b>Twitter Monitor Started</b>\n\n"
        f"Monitoring {len(accounts)} accounts\n"
        f"Check interval: {check_interval}s per account\n"
        f"Notifying for posts under {recent_minutes} minutes old"
    )

    try:
        while True:
            cycle_number += 1
            print(f"\n{'='*70}")
            print(f"CYCLE #{cycle_number} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")

            monitor_accounts(
                api_client=api_client,
                notifier=notifier,
                accounts=accounts,
                recent_minutes=recent_minutes,
                check_interval=check_interval,
                state=state
            )

            print(f"Cycle #{cycle_number} complete. Starting next cycle...\n")

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping monitor...")
        try:
            notifier.send_message_sync("🛑 <b>Twitter Monitor Stopped</b>")
        except Exception as e:
            print(f"  Note: Could not send shutdown notification: {e}")
        print("✓ Goodbye!")

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the monitor service."""
    print("=" * 70)
    print("Twitter Monitor - TwitterAPI.io")
    print("=" * 70)
    print()

    # Load configuration
    try:
        config = load_config()
        api_key = config['api']['key']
        bot_token = config['telegram']['bot_token']
        chat_id = config['telegram']['chat_id']
        recent_minutes = config['monitoring']['recent_post_minutes']
        check_interval = config['monitoring']['check_interval_seconds']

    except KeyError as e:
        print(f"❌ Missing configuration: {e}")
        print("Please check your config.json file")
        return

    except FileNotFoundError:
        print("❌ config.json not found")
        print("Please create config.json with your API keys")
        return

    # Load accounts
    accounts = load_accounts()

    if not accounts:
        print("❌ No accounts to monitor")
        print("Run: python account_scraper.py")
        return

    print(f"✓ Loaded {len(accounts)} accounts")
    print(f"✓ API key configured")
    print(f"✓ Telegram bot configured")
    print()

    # Initialize clients
    api_client = TwitterAPIClient(api_key)
    notifier = TelegramNotifier(bot_token, chat_id)

    # Test API connection
    print("Testing API connection...")
    try:
        test_result = api_client.get_latest_tweet_info(accounts[0])
        print(f"✓ API connection successful")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print("Please check your API key")
        return

    print()

    # Start monitoring
    run_continuous_monitoring(
        api_client=api_client,
        notifier=notifier,
        accounts=accounts,
        recent_minutes=recent_minutes,
        check_interval=check_interval
    )


if __name__ == "__main__":
    main()
