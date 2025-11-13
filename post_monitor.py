#!/usr/bin/env python3
"""
Post Monitor - Monitors Twitter/X accounts for recent posts using TwitterAPI.io
"""

import json
import time
import csv
from datetime import datetime
from twitterapi_io.client import TwitterAPIClient
from notifier import TelegramNotifier
from monitor_state import MonitorState


def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        return json.load(f)


def load_accounts(filename='accounts.csv'):
    """Load accounts to monitor from CSV or text file"""
    accounts = []

    # Try CSV first (from account_scraper.py)
    if filename.endswith('.csv'):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and not row[0].startswith('#'):
                        username = row[0].strip()
                        # Skip header and empty lines
                        if username and username != 'username':
                            username = username.lstrip('@')
                            accounts.append(username)
            print(f"Loaded {len(accounts)} accounts to monitor from CSV")
            return accounts
        except FileNotFoundError:
            # Try .txt file as fallback
            txt_filename = filename.replace('.csv', '.txt')
            try:
                return load_accounts(txt_filename)
            except:
                print(f"ERROR: {filename} not found.")
                print("Run account_scraper.py to generate accounts.csv")
                return []
    else:
        # Load from text file
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Remove @ if present
                        username = line.lstrip('@')
                        accounts.append(username)
            print(f"Loaded {len(accounts)} accounts to monitor from TXT")
            return accounts
        except FileNotFoundError:
            print(f"ERROR: {filename} not found.")
            print("Create accounts.txt with one username per line.")
            return []


def monitor_accounts(api_client, notifier, accounts, recent_minutes, check_interval, state):
    """
    Check accounts for recent posts.

    Args:
        api_client: TwitterAPIClient instance
        notifier: TelegramNotifier instance
        accounts: List of usernames to monitor
        recent_minutes: Only notify if post is within this many minutes
        check_interval: Seconds to wait between checking each account
        state: MonitorState instance for tracking notifications and cooldowns
    """
    # Filter out accounts in cooldown
    accounts_to_check = []
    accounts_in_cooldown = []

    for username in accounts:
        if state.is_in_cooldown(username, cooldown_minutes=recent_minutes):
            remaining = state.get_cooldown_remaining(username, cooldown_minutes=recent_minutes)
            accounts_in_cooldown.append((username, remaining))
        else:
            accounts_to_check.append(username)

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking {len(accounts_to_check)} accounts...")
    print(f"Will notify for posts under {recent_minutes} minutes old")
    if accounts_in_cooldown:
        print(f"Skipping {len(accounts_in_cooldown)} accounts in cooldown")
    print(f"Checking 1 account every {check_interval} seconds\n")

    recent_posts_found = 0

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
        print(f"[{i}/{len(accounts_to_check)}] Checking @{username}...")

        rate_limited = False
        notification_sent = False

        try:
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
                    recent_posts_found += 1

                    # Send notification
                    success = notifier.send_new_post_notification_sync(
                        username=username,
                        post_url=recent_post['url'],
                        post_text=recent_post['text'][:200]
                    )
                    if success:
                        print(f"  ✓ Telegram notification sent")
                        notification_sent = True

                        # Mark as notified and set cooldown
                        if tweet_id:
                            state.mark_as_notified(tweet_id, username)
                            print(f"  ✓ Cooldown activated ({recent_minutes} minutes)")
                    else:
                        print(f"  ⚠️  Telegram notification failed")

            else:
                print(f"  None found in the past {recent_minutes} minutes")

        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Error: {error_msg}")

            # Check if rate limited
            if "Rate limit exceeded" in error_msg:
                rate_limited = True

        # Only wait if we sent a notification or got rate limited (unless it's the last account)
        if i < len(accounts):
            if rate_limited or notification_sent:
                elapsed = time.time() - cycle_start
                sleep_time = max(0, check_interval - elapsed)

                # If rate limited, wait extra time
                if rate_limited:
                    sleep_time = max(sleep_time, 60)  # Wait at least 60 seconds
                    print(f"  ⏳ Rate limited! Waiting {sleep_time:.0f} seconds...\n")
                elif sleep_time > 0:
                    print(f"  Waiting {sleep_time:.0f} seconds before next check...\n")
                else:
                    print()

                time.sleep(sleep_time) if sleep_time > 0 else None
            else:
                # No notification sent and not rate limited - continue immediately
                print()

    if recent_posts_found > 0:
        print(f"\n✓ Found {recent_posts_found} recent post(s)!")
    else:
        print("\n✓ No recent posts found")


def main():
    """Main monitoring loop"""
    print("=" * 70)
    print("Twitter/X Recent Post Monitor - TwitterAPI.io")
    print("=" * 70)

    # Load configuration
    try:
        config = load_config()
        check_interval = config['monitoring']['check_interval_seconds']
        recent_minutes = config['monitoring']['recent_post_minutes']
        bot_token = config['telegram']['bot_token']
        chat_id = config['telegram']['chat_id']
        api_key = config['api']['key']

    except KeyError as e:
        print(f"ERROR: Missing configuration: {e}")
        print("Please check your config.json file")
        return

    except FileNotFoundError:
        print("ERROR: config.json not found")
        return

    # Load accounts
    accounts = load_accounts()
    if not accounts:
        print("ERROR: No accounts to monitor")
        print("Run account_scraper.py to generate accounts.csv")
        return

    # Initialize clients
    api_client = TwitterAPIClient(api_key)
    notifier = TelegramNotifier(bot_token, chat_id)

    # Initialize state manager
    state = MonitorState()
    stats = state.get_stats()

    # Calculate cycle time
    total_cycle_time = len(accounts) * check_interval
    cycle_minutes = total_cycle_time / 60
    cycle_hours = cycle_minutes / 60

    print(f"\nConfiguration:")
    print(f"  Accounts: {len(accounts)}")
    print(f"  Check interval: {check_interval} seconds between accounts")
    print(f"  Recent threshold: {recent_minutes} minutes")
    print(f"  Cooldown period: {recent_minutes} minutes after notification")
    print(f"  Estimated cycle time: {cycle_minutes:.1f} minutes ({cycle_hours:.1f} hours)")
    print(f"\nState:")
    print(f"  Tweets tracked: {stats['total_tweets_tracked']}")
    print(f"  Accounts in cooldown: {stats['accounts_in_cooldown']}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)

    try:
        # Send startup notification
        notifier.send_message_sync(
            "🤖 <b>Post Monitor Started</b>\n\n"
            f"Monitoring {len(accounts)} accounts\n"
            f"Checking 1 account every {check_interval}s\n"
            f"Full cycle: {cycle_minutes:.1f} min\n"
            f"Notifying for posts under {recent_minutes} min old"
        )

        # Main monitoring loop
        cycle_num = 0
        while True:
            cycle_num += 1
            print(f"\n{'='*70}")
            print(f"CYCLE #{cycle_num}")
            print(f"{'='*70}")

            try:
                monitor_accounts(api_client, notifier, accounts, recent_minutes, check_interval, state)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error in monitoring cycle: {e}")
                import traceback
                traceback.print_exc()
                print("Continuing to next cycle...")

            print(f"\n✓ Cycle #{cycle_num} complete. Starting next cycle...\n")

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping monitor...")
        try:
            notifier.send_message_sync("🛑 <b>Post Monitor Stopped</b>")
        except Exception as e:
            print(f"  Note: Could not send shutdown notification: {e}")
        print("✓ Goodbye!")

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
