#!/usr/bin/env python3
"""
Cost-Effective Twitter Monitor using Advanced Search API

Instead of checking each account individually (43 API calls per cycle),
this uses Advanced Search to check all accounts in 1-2 API calls per cycle.

Cost comparison:
- Old method: 43 calls/cycle × 12 cycles/hour = 516 calls/hour = ~$1.50/hour
- New method: 2 calls/cycle × 12 cycles/hour = 24 calls/hour = ~$0.07/hour

Savings: ~95% reduction in API costs!
"""

import json
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from twitterapi_io.advanced_monitor import AdvancedTwitterMonitor, load_accounts, load_config
from notifier import TelegramNotifier


def monitor_cycle(
    monitor: AdvancedTwitterMonitor,
    notifier: TelegramNotifier,
    accounts: List[str],
    check_interval_minutes: int,
    notify_threshold_minutes: int
):
    """
    Run one monitoring cycle using Advanced Search.

    Args:
        monitor: AdvancedTwitterMonitor instance
        notifier: TelegramNotifier instance
        accounts: List of usernames to monitor
        check_interval_minutes: How far back to search for tweets (search window)
        notify_threshold_minutes: Only notify for posts this recent
    """
    print(f"\n{'='*70}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting check cycle")
    print(f"{'='*70}\n")

    print(f"Checking {len(accounts)} accounts")
    print(f"Time window: last {check_interval_minutes} minutes")
    print(f"Will notify for posts under {notify_threshold_minutes} minutes old\n")

    # Check all accounts (rate limit enforced internally)
    try:
        all_tweets = monitor.check_accounts_for_new_tweets(
            accounts,
            time_window_minutes=check_interval_minutes
        )
    except Exception as e:
        print(f"  ❌ Error: {e}")
        all_tweets = []

    print(f"\n{'─'*70}")
    print(f"Total tweets found: {len(all_tweets)}")

    # Filter tweets by age and send notifications
    notifications_sent = 0
    now = datetime.now(timezone.utc)

    for tweet in all_tweets:
        # Parse tweet time
        try:
            # Format: "Thu Nov 13 16:25:20 +0000 2025"
            tweet_time = datetime.strptime(tweet['created_at'], "%a %b %d %H:%M:%S %z %Y")
            time_diff = now - tweet_time
            minutes_ago = time_diff.total_seconds() / 60

            # Check if within notification threshold
            if minutes_ago <= notify_threshold_minutes:
                print(f"\n🚨 RECENT POST from @{tweet['username']}!")
                print(f"   Posted {minutes_ago:.1f} minutes ago")
                print(f"   URL: {tweet['url']}")

                # Send notification
                success = notifier.send_new_post_notification_sync(
                    username=tweet['username'],
                    post_url=tweet['url'],
                    post_text=tweet['text'][:200]
                )

                if success:
                    print(f"   ✓ Telegram notification sent")
                    notifications_sent += 1
                else:
                    print(f"   ⚠️  Telegram notification failed")

        except Exception as e:
            print(f"   Error processing tweet: {e}")

    print(f"\n{'─'*70}")
    if notifications_sent > 0:
        print(f"✓ Sent {notifications_sent} notification(s)")
    else:
        print(f"✓ No recent posts found (within {notify_threshold_minutes} minutes)")
    print(f"{'='*70}\n")


def main():
    """Main monitoring loop"""
    print("=" * 70)
    print("Advanced Twitter Monitor - Cost-Effective Mode")
    print("=" * 70)
    print()

    # Load configuration
    try:
        config = load_config()
        check_interval = config['monitoring']['check_interval_seconds']
        notify_threshold = config['monitoring']['recent_post_minutes']
        api_key = config['api']['key']
        rate_limit = config['api'].get('rate_limit_seconds', 6.0)
        bot_token = config['telegram']['bot_token']
        chat_id = config['telegram']['chat_id']

    except KeyError as e:
        print(f"❌ Missing configuration: {e}")
        return

    except FileNotFoundError:
        print("❌ config.json not found")
        return

    # Load accounts
    accounts = load_accounts()

    if not accounts:
        print("❌ No accounts to monitor")
        print("Run: python account_scraper.py")
        return

    # Initialize
    monitor = AdvancedTwitterMonitor(api_key, min_delay=rate_limit)
    notifier = TelegramNotifier(bot_token, chat_id)

    # Use notify_threshold as the search window (how far back to look)
    # Use check_interval for how often to run cycles
    search_window_minutes = notify_threshold
    check_interval_minutes = check_interval // 60
    if check_interval_minutes < 1:
        check_interval_minutes = max(1, check_interval_minutes)

    print(f"Configuration:")
    print(f"  Accounts: {len(accounts)}")
    print(f"  Check interval: {check_interval} seconds")
    print(f"  Search window: {search_window_minutes} minute(s)")
    print(f"  Notification threshold: {notify_threshold} minute(s)")
    print(f"  API calls per cycle: {len(accounts)}")
    print(f"  Rate limit: {rate_limit} seconds between calls")
    print(f"  Estimated cycle time: {len(accounts) * rate_limit / 60:.1f} minutes")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)

    # Send startup notification
    try:
        notifier.send_message_sync(
            "🤖 <b>Advanced Monitor Started</b>\n\n"
            f"Monitoring {len(accounts)} accounts\n"
            f"Check every: {check_interval}s\n"
            f"Search window: {search_window_minutes} min\n"
            f"Notify threshold: {notify_threshold} min\n"
            f"Rate limit: {rate_limit}s between calls"
        )
    except Exception as e:
        print(f"Note: Could not send startup notification: {e}")

    # Main monitoring loop
    cycle_num = 0

    try:
        while True:
            cycle_num += 1

            monitor_cycle(
                monitor=monitor,
                notifier=notifier,
                accounts=accounts,
                check_interval_minutes=search_window_minutes,
                notify_threshold_minutes=notify_threshold
            )

            # Wait until next cycle
            print(f"Waiting {check_interval} seconds until next cycle...")
            print(f"(Next cycle will be #{cycle_num + 1})\n")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping monitor...")
        try:
            notifier.send_message_sync("🛑 <b>Advanced Monitor Stopped</b>")
        except Exception as e:
            print(f"  Note: Could not send shutdown notification: {e}")
        print("✓ Goodbye!")

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
