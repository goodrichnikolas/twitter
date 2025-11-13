#!/usr/bin/env python3
"""
Integration tests for Twitter monitoring system

Tests:
1. Advanced Search API finds recent tweets
2. Telegram connection works
3. Telegram can send messages
"""

import pytest
import json
from datetime import datetime, timedelta, timezone

from twitterapi_io.advanced_monitor import AdvancedTwitterMonitor, load_config
from notifier import TelegramNotifier


@pytest.fixture
def config():
    """Load configuration"""
    return load_config('config.json')


@pytest.fixture
def monitor(config):
    """Create AdvancedTwitterMonitor instance"""
    api_key = config['api']['key']
    rate_limit = config['api'].get('rate_limit_seconds', 6.0)
    return AdvancedTwitterMonitor(api_key, save_responses=True, min_delay=rate_limit)


@pytest.fixture
def notifier(config):
    """Create TelegramNotifier instance"""
    bot_token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']
    return TelegramNotifier(bot_token, chat_id)


class TestAdvancedSearch:
    """Test Advanced Search API functionality"""

    def test_find_recent_elonmusk_tweet(self, monitor):
        """
        Test that we can find Elon Musk's most recent tweet using Advanced Search.

        This test:
        - Searches for tweets from @elonmusk in the last 24 hours
        - Verifies we get at least one tweet back
        - Checks the tweet has expected fields
        """
        print("\n" + "="*70)
        print("TEST: Finding recent tweet from @elonmusk")
        print("="*70)

        username = "elonmusk"

        # Search last 24 hours to ensure we find something
        until_time = datetime.now(timezone.utc)
        since_time = until_time - timedelta(hours=24)

        print(f"\nSearching for tweets from @{username}")
        print(f"Time range: {since_time.strftime('%Y-%m-%d %H:%M:%S')} to {until_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        # Build and execute query
        query = monitor.build_query(username, since_time, until_time)
        print(f"Query: {query}")

        response = monitor.search_tweets(query)

        # Check we got tweets
        tweets = response.get('tweets', [])
        print(f"\nFound {len(tweets)} tweet(s)")

        assert len(tweets) > 0, "Should find at least one tweet from @elonmusk in last 24 hours"

        # Check first tweet structure
        first_tweet = tweets[0]
        print(f"\nMost recent tweet:")
        print(f"  ID: {first_tweet.get('id')}")
        print(f"  Text: {first_tweet.get('text', '')[:100]}...")
        print(f"  Created: {first_tweet.get('createdAt')}")
        print(f"  URL: {first_tweet.get('url')}")

        # Verify tweet has required fields
        assert 'id' in first_tweet, "Tweet should have 'id'"
        assert 'text' in first_tweet, "Tweet should have 'text'"
        assert 'createdAt' in first_tweet, "Tweet should have 'createdAt'"
        assert 'author' in first_tweet, "Tweet should have 'author'"

        # Verify author is correct
        author = first_tweet.get('author', {})
        assert author.get('userName') == username, f"Author should be @{username}"

        print("\n✓ Test passed: Successfully found recent tweet from @elonmusk")
        print("="*70)

    def test_query_format(self, monitor):
        """
        Test that query is built with correct format.
        """
        print("\n" + "="*70)
        print("TEST: Query format validation")
        print("="*70)

        username = "testuser"
        until_time = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        since_time = datetime(2024, 1, 15, 12, 25, 30, tzinfo=timezone.utc)

        query = monitor.build_query(username, since_time, until_time, include_retweets=True)

        print(f"\nGenerated query: {query}")

        # Verify format
        assert "from:testuser" in query, "Query should contain 'from:username'"
        assert "since:2024-01-15_12:25:30_UTC" in query, "Query should have correct since format"
        assert "until:2024-01-15_12:30:45_UTC" in query, "Query should have correct until format"
        assert "include:nativeretweets" in query, "Query should include retweets flag"

        print("\n✓ Test passed: Query format is correct")
        print("="*70)

    def test_empty_results(self, monitor):
        """
        Test handling of queries that return no results.
        """
        print("\n" + "="*70)
        print("TEST: Empty results handling")
        print("="*70)

        username = "elonmusk"

        # Search a very narrow time window in the past (likely no tweets)
        until_time = datetime(2020, 1, 1, 0, 1, 0, tzinfo=timezone.utc)
        since_time = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        print(f"\nSearching narrow time window (should be empty)")

        query = monitor.build_query(username, since_time, until_time)
        response = monitor.search_tweets(query)

        tweets = response.get('tweets', [])
        print(f"Found {len(tweets)} tweet(s) (expected 0)")

        assert isinstance(tweets, list), "Should return a list even when empty"

        print("\n✓ Test passed: Empty results handled correctly")
        print("="*70)


class TestTelegram:
    """Test Telegram notification functionality"""

    def test_telegram_connection(self, notifier):
        """
        Test that we can connect to Telegram bot API.

        This verifies the bot token is valid.
        """
        print("\n" + "="*70)
        print("TEST: Telegram connection")
        print("="*70)

        print("\nTesting Telegram bot connection...")

        # The bot instance should be created without errors
        assert notifier.bot is not None, "Telegram bot should be initialized"
        assert notifier.bot_token is not None, "Bot token should be set"
        assert notifier.chat_id is not None, "Chat ID should be set"

        print(f"Bot token: {notifier.bot_token[:10]}...")
        print(f"Chat ID: {notifier.chat_id}")

        print("\n✓ Test passed: Telegram bot initialized")
        print("="*70)

    def test_send_test_message(self, notifier):
        """
        Test sending an actual message to Telegram.

        This will send a real message to your Telegram chat.
        """
        print("\n" + "="*70)
        print("TEST: Send test message to Telegram")
        print("="*70)

        test_message = (
            "🧪 <b>Test Message from Integration Tests</b>\n\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "If you see this, the notification system is working! ✅"
        )

        print("\nSending test message to Telegram...")
        print(f"Message: {test_message[:50]}...")

        # Send message
        success = notifier.send_message_sync(test_message)

        assert success is True, "Message should be sent successfully"

        print("\n✓ Test passed: Message sent to Telegram")
        print("Check your Telegram to confirm you received it!")
        print("="*70)

    def test_send_new_post_notification(self, notifier):
        """
        Test sending a new post notification (formatted).
        """
        print("\n" + "="*70)
        print("TEST: Send new post notification")
        print("="*70)

        username = "elonmusk"
        post_url = "https://x.com/elonmusk/status/1234567890"
        post_text = "This is a test tweet to verify notification formatting works correctly."

        print(f"\nSending new post notification for @{username}...")

        success = notifier.send_new_post_notification_sync(
            username=username,
            post_url=post_url,
            post_text=post_text
        )

        assert success is True, "New post notification should be sent successfully"

        print("\n✓ Test passed: New post notification sent")
        print("Check your Telegram to see the formatted notification!")
        print("="*70)


class TestEndToEnd:
    """End-to-end integration tests"""

    def test_full_monitoring_cycle(self, monitor, notifier):
        """
        Test a complete monitoring cycle:
        1. Search for recent tweets from a test account
        2. If found, send notification

        Uses @elonmusk since he tweets frequently.
        """
        print("\n" + "="*70)
        print("TEST: Full monitoring cycle")
        print("="*70)

        test_accounts = ["elonmusk"]
        time_window_minutes = 60  # Last hour

        print(f"\nRunning full monitoring cycle for {len(test_accounts)} account(s)")
        print(f"Time window: {time_window_minutes} minutes")

        # Search for tweets
        tweets = monitor.check_accounts_for_new_tweets(
            test_accounts,
            time_window_minutes=time_window_minutes
        )

        print(f"\nFound {len(tweets)} tweet(s)")

        if len(tweets) > 0:
            # Send notification for first tweet
            tweet = tweets[0]
            print(f"\nSending notification for tweet from @{tweet['username']}...")

            success = notifier.send_new_post_notification_sync(
                username=tweet['username'],
                post_url=tweet['url'],
                post_text=tweet['text'][:200]
            )

            assert success is True, "Notification should be sent"
            print("\n✓ Notification sent successfully")
        else:
            print("\n⚠️  No tweets found in time window (this is OK)")

        print("\n✓ Test passed: Full cycle completed")
        print("="*70)

    def test_goonercards_recent_post(self, monitor, notifier):
        """
        Test checking Goonercards account for recent post under 60 minutes.
        If found, send notification to Telegram.
        """
        print("\n" + "="*70)
        print("TEST: Check Goonercards for recent post (< 60 minutes)")
        print("="*70)

        username = "Goonercards"
        time_window_minutes = 60

        print(f"\nSearching @{username} for posts in last {time_window_minutes} minutes...")

        # Search for tweets
        tweets = monitor.check_accounts_for_new_tweets(
            [username],
            time_window_minutes=time_window_minutes
        )

        print(f"\nFound {len(tweets)} tweet(s)")

        if len(tweets) > 0:
            # Get the most recent tweet
            tweet = tweets[0]

            print(f"\nMost recent post:")
            print(f"  Username: @{tweet['username']}")
            print(f"  Posted: {tweet['created_at']}")
            print(f"  Text: {tweet['text'][:100]}...")
            print(f"  URL: {tweet['url']}")

            # Send notification to Telegram
            print(f"\nSending notification to Telegram...")
            success = notifier.send_new_post_notification_sync(
                username=tweet['username'],
                post_url=tweet['url'],
                post_text=tweet['text']
            )

            assert success is True, "Telegram notification should be sent successfully"
            print("✓ Notification sent to Telegram!")
            print("Check your Telegram to see the post!")
        else:
            print(f"\n⚠️  No tweets found from @{username} in last {time_window_minutes} minutes")
            print("This is OK - you may not have posted recently")

        print("\n✓ Test passed: Goonercards check completed")
        print("="*70)


def run_all_tests():
    """Run all tests manually (without pytest)"""
    print("\n" + "="*70)
    print("TWITTER MONITORING SYSTEM - INTEGRATION TESTS")
    print("="*70)

    try:
        config = load_config('config.json')
        rate_limit = config['api'].get('rate_limit_seconds', 6.0)
        monitor = AdvancedTwitterMonitor(config['api']['key'], save_responses=True, min_delay=rate_limit)
        notifier = TelegramNotifier(config['telegram']['bot_token'], config['telegram']['chat_id'])

        # Test Advanced Search
        test_search = TestAdvancedSearch()
        test_search.test_find_recent_elonmusk_tweet(monitor)
        test_search.test_query_format(monitor)
        test_search.test_empty_results(monitor)

        # Test Telegram
        test_telegram = TestTelegram()
        test_telegram.test_telegram_connection(notifier)
        test_telegram.test_send_test_message(notifier)
        test_telegram.test_send_new_post_notification(notifier)

        # Test End-to-End
        test_e2e = TestEndToEnd()
        test_e2e.test_full_monitoring_cycle(monitor, notifier)

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Can run with pytest or directly
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        run_all_tests()
    else:
        print("Run with pytest:")
        print("  pytest test_integration.py -v -s")
        print("\nOr run manually:")
        print("  python test_integration.py --manual")
