#!/usr/bin/env python3
"""
Monitor State Management

Tracks:
1. Tweet IDs that have been notified (prevent duplicates)
2. Last notification time per account (for cooldown periods)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Set, Dict, Optional


class MonitorState:
    """Manages monitoring state to prevent duplicate notifications"""

    def __init__(self, state_file: str = 'monitor_state.json'):
        """
        Initialize state manager.

        Args:
            state_file: Path to state file
        """
        self.state_file = Path(state_file)
        self.notified_tweets: Set[str] = set()  # Tweet IDs we've notified
        self.last_notification: Dict[str, float] = {}  # username -> timestamp
        self._load_state()

    def _load_state(self):
        """Load state from file."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.notified_tweets = set(data.get('notified_tweets', []))
                self.last_notification = data.get('last_notification', {})
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")

    def _save_state(self):
        """Save state to file."""
        try:
            data = {
                'notified_tweets': list(self.notified_tweets),
                'last_notification': self.last_notification
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state file: {e}")

    def has_been_notified(self, tweet_id: str) -> bool:
        """
        Check if we've already sent a notification for this tweet.

        Args:
            tweet_id: Tweet ID to check

        Returns:
            True if already notified, False otherwise
        """
        return tweet_id in self.notified_tweets

    def mark_as_notified(self, tweet_id: str, username: str):
        """
        Mark a tweet as notified and update last notification time.

        Args:
            tweet_id: Tweet ID
            username: Account username
        """
        self.notified_tweets.add(tweet_id)
        self.last_notification[username] = datetime.now(timezone.utc).timestamp()
        self._save_state()

    def is_in_cooldown(self, username: str, cooldown_minutes: int = 180) -> bool:
        """
        Check if an account is in cooldown period.

        Args:
            username: Account username
            cooldown_minutes: Cooldown period in minutes

        Returns:
            True if in cooldown, False otherwise
        """
        if username not in self.last_notification:
            return False

        last_notified = self.last_notification[username]
        now = datetime.now(timezone.utc).timestamp()
        elapsed_minutes = (now - last_notified) / 60

        return elapsed_minutes < cooldown_minutes

    def get_cooldown_remaining(self, username: str, cooldown_minutes: int = 180) -> Optional[float]:
        """
        Get remaining cooldown time in minutes.

        Args:
            username: Account username
            cooldown_minutes: Cooldown period in minutes

        Returns:
            Remaining minutes, or None if not in cooldown
        """
        if username not in self.last_notification:
            return None

        last_notified = self.last_notification[username]
        now = datetime.now(timezone.utc).timestamp()
        elapsed_minutes = (now - last_notified) / 60
        remaining = cooldown_minutes - elapsed_minutes

        return remaining if remaining > 0 else None

    def cleanup_old_tweets(self, max_tweets: int = 10000):
        """
        Cleanup old tweet IDs to prevent memory bloat.
        Keeps only the most recent N tweets.

        Args:
            max_tweets: Maximum number of tweet IDs to keep
        """
        if len(self.notified_tweets) > max_tweets:
            # Convert to list, keep the last N items
            tweets_list = list(self.notified_tweets)
            self.notified_tweets = set(tweets_list[-max_tweets:])
            self._save_state()

    def get_stats(self) -> Dict:
        """
        Get state statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'total_tweets_tracked': len(self.notified_tweets),
            'accounts_with_notifications': len(self.last_notification),
            'accounts_in_cooldown': sum(
                1 for username in self.last_notification
                if self.is_in_cooldown(username, cooldown_minutes=180)
            )
        }


def main():
    """Test the state manager"""
    state = MonitorState()

    print("Monitor State Statistics")
    print("=" * 70)
    stats = state.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\nAccounts in cooldown:")
    for username in state.last_notification:
        remaining = state.get_cooldown_remaining(username, cooldown_minutes=180)
        if remaining:
            print(f"  @{username}: {remaining:.1f} minutes remaining")


if __name__ == "__main__":
    main()
