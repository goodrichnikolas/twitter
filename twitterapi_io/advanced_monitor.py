#!/usr/bin/env python3
"""
Advanced Twitter Monitor using TwitterAPI.io Advanced Search
Much more cost-effective than individual account checks
"""

import json
import time
import csv
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from pathlib import Path


class AdvancedTwitterMonitor:
    """
    Monitor multiple Twitter accounts using Advanced Search API.
    More cost-effective: 1-2 API calls per cycle vs 1 call per account.
    """

    BASE_URL = "https://api.twitterapi.io"

    def __init__(self, api_key: str, save_responses: bool = True, min_delay: float = 0.05):
        """
        Initialize the monitor.

        Args:
            api_key: TwitterAPI.io API key
            save_responses: Save API responses to jsons/ folder
            min_delay: Minimum seconds between API calls (default: 0.05 for 20 calls/sec)
        """
        self.api_key = api_key
        self.save_responses = save_responses
        self.min_delay = min_delay
        self.last_call_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })

        # Create jsons folder if needed
        if self.save_responses:
            Path("jsons").mkdir(exist_ok=True)

    def _save_response(self, query_id: str, response_data: Dict):
        """Save API response to jsons/ folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"jsons/advanced_search_{query_id}_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  Warning: Could not save response: {e}")

    def build_query(
        self,
        username: str,
        since_time: datetime,
        until_time: datetime,
        include_retweets: bool = True
    ) -> str:
        """
        Build an Advanced Search query for a single account.

        Args:
            username: Twitter username to monitor
            since_time: Start time for search window
            until_time: End time for search window
            include_retweets: Whether to include retweets

        Returns:
            Query string for Advanced Search API
        """
        # Format times as YYYY-MM-DD_HH:MM:SS_UTC
        since_str = since_time.strftime('%Y-%m-%d_%H:%M:%S_UTC')
        until_str = until_time.strftime('%Y-%m-%d_%H:%M:%S_UTC')

        # Build query for single user
        # Example: from:elonmusk since:2024-01-01_12:00:00_UTC until:2024-01-01_12:05:00_UTC
        query = f"from:{username} since:{since_str} until:{until_str}"

        if include_retweets:
            query += " include:nativeretweets"

        return query

    def _enforce_rate_limit(self):
        """Ensure minimum delay between API calls."""
        import time as time_module
        elapsed = time_module.time() - self.last_call_time
        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed
            print(f"  [Rate limit] Waiting {sleep_time:.1f}s before API call...")
            time_module.sleep(sleep_time)
        self.last_call_time = time_module.time()

    def search_tweets(
        self,
        query: str,
        query_type: str = "Latest"
    ) -> Dict:
        """
        Execute an Advanced Search query.

        Args:
            query: Advanced Search query string
            query_type: "Latest" or "Top" (default: Latest)

        Returns:
            API response with tweets
        """
        # Enforce rate limiting
        self._enforce_rate_limit()

        endpoint = f"{self.BASE_URL}/twitter/tweet/advanced_search"

        params = {
            "query": query,
            "queryType": query_type,
            "cursor": ""
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            response_data = response.json()

            # Save response
            if self.save_responses:
                query_id = hash(query) % 100000  # Simple ID from query
                self._save_response(str(query_id), response_data)

            return response_data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = e.response.headers.get('Retry-After', '60')
                raise Exception(f"Rate limit exceeded. Retry after {retry_after}s") from e
            elif e.response.status_code == 401:
                raise Exception("Invalid API key") from e
            else:
                raise Exception(f"API error: {e.response.status_code}") from e

        except requests.exceptions.Timeout:
            raise Exception("API request timed out")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}") from e

    def check_accounts_for_new_tweets(
        self,
        usernames: List[str],
        time_window_minutes: int = 5
    ) -> List[Dict]:
        """
        Check multiple accounts for new tweets in a time window.
        Makes one API call per account due to query limitations.

        Args:
            usernames: List of usernames to check
            time_window_minutes: How many minutes back to check

        Returns:
            List of new tweets found
        """
        # Define time window
        until_time = datetime.now(timezone.utc)
        since_time = until_time - timedelta(minutes=time_window_minutes)

        print(f"  Time window: {since_time.strftime('%H:%M:%S')} to {until_time.strftime('%H:%M:%S')} UTC")
        print(f"  Checking {len(usernames)} accounts individually...")

        all_parsed_tweets = []

        # Check each account separately
        for i, username in enumerate(usernames, 1):
            try:
                # Build query for this user
                query = self.build_query(username, since_time, until_time)

                print(f"    [{i}/{len(usernames)}] @{username}: {query[:80]}...")

                # Execute search
                response = self.search_tweets(query)

                # Extract tweets
                tweets = response.get('tweets', [])

                if tweets:
                    print(f"      → Found {len(tweets)} tweet(s)")

                    # Parse tweets
                    for tweet in tweets:
                        author = tweet.get('author', {})
                        tweet_username = author.get('userName', username)

                        all_parsed_tweets.append({
                            'username': tweet_username,
                            'tweet_id': tweet.get('id'),
                            'text': tweet.get('text', ''),
                            'created_at': tweet.get('createdAt'),
                            'url': tweet.get('url', f"https://x.com/{tweet_username}/status/{tweet.get('id')}"),
                            'like_count': tweet.get('likeCount', 0),
                            'retweet_count': tweet.get('retweetCount', 0)
                        })

            except Exception as e:
                print(f"      → Error: {e}")
                continue

        print(f"  Total tweets found: {len(all_parsed_tweets)}")
        return all_parsed_tweets

    def split_accounts_into_batches(
        self,
        usernames: List[str],
        batch_size: int = 20
    ) -> List[List[str]]:
        """
        Split accounts into batches to avoid query length limits.

        Args:
            usernames: List of all usernames
            batch_size: Maximum accounts per batch

        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(usernames), batch_size):
            batches.append(usernames[i:i + batch_size])
        return batches


def load_accounts(csv_path: str = 'accounts.csv') -> List[str]:
    """Load accounts from CSV file."""
    accounts = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    username = row[0].strip()
                    if username and username != 'username':
                        username = username.lstrip('@')
                        accounts.append(username)
        return accounts

    except FileNotFoundError:
        print(f"ERROR: {csv_path} not found")
        return []


def load_config(config_path: str = 'config.json') -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Test the advanced monitor"""
    print("=" * 70)
    print("Advanced Twitter Monitor - Test")
    print("=" * 70)
    print()

    # Load config
    config = load_config()
    api_key = config['api']['key']

    # Load accounts
    accounts = load_accounts()
    print(f"Loaded {len(accounts)} accounts")
    print()

    # Initialize monitor
    monitor = AdvancedTwitterMonitor(api_key)

    # Check for new tweets in last 60 minutes
    print("Checking for tweets in last 60 minutes...")
    new_tweets = monitor.check_accounts_for_new_tweets(accounts, time_window_minutes=60)

    print()
    print(f"Found {len(new_tweets)} tweets:")
    for tweet in new_tweets:
        print(f"  @{tweet['username']}: {tweet['text'][:60]}...")
        print(f"    URL: {tweet['url']}")
        print()


if __name__ == "__main__":
    main()
