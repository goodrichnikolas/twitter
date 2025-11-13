#!/usr/bin/env python3
"""
Get User Followings - Fetch accounts a user is following

Uses TwitterAPI.io to get the list of accounts that a user follows
and adds them to accounts.csv.

Usage:
    python get_followers.py --user elonmusk
    python get_followers.py --user elonmusk --max 100
"""

import argparse
import csv
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Set, Optional


class FollowingsClient:
    """Client for fetching user followings from TwitterAPI.io"""

    BASE_URL = "https://api.twitterapi.io"

    def __init__(self, api_key: str, min_delay: float = 0.05):
        """
        Initialize the client.

        Args:
            api_key: TwitterAPI.io API key
            min_delay: Minimum seconds between API calls (default: 0.05 for 20 calls/sec)
        """
        self.api_key = api_key
        self.min_delay = min_delay
        self.last_call_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })

    def _enforce_rate_limit(self):
        """Ensure minimum delay between API calls."""
        import time as time_module
        elapsed = time_module.time() - self.last_call_time
        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed
            time_module.sleep(sleep_time)
        self.last_call_time = time_module.time()

    def get_followings_page(
        self,
        username: str,
        cursor: str = "",
        page_size: int = 200
    ) -> Dict:
        """
        Get a single page of followings for a user.

        Args:
            username: Twitter username to get followings for
            cursor: Pagination cursor (empty string for first page)
            page_size: Number of results per page (20-200, default: 200)

        Returns:
            API response with followings, has_next_page, next_cursor
        """
        # Enforce rate limiting
        self._enforce_rate_limit()

        endpoint = f"{self.BASE_URL}/twitter/user/followings"

        params = {
            "userName": username,
            "cursor": cursor,
            "pageSize": page_size
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            return response_data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = e.response.headers.get('Retry-After', '60')
                raise Exception(f"Rate limit exceeded. Retry after {retry_after}s") from e
            elif e.response.status_code == 401:
                raise Exception("Invalid API key") from e
            elif e.response.status_code == 400:
                error_data = e.response.json()
                raise Exception(f"Bad request: {error_data.get('message', 'Unknown error')}") from e
            else:
                raise Exception(f"API error: {e.response.status_code}") from e

        except requests.exceptions.Timeout:
            raise Exception("API request timed out")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}") from e

    def get_all_followings(
        self,
        username: str,
        max_followings: Optional[int] = None,
        page_size: int = 200
    ) -> List[Dict]:
        """
        Get all followings for a user (with pagination).

        Args:
            username: Twitter username to get followings for
            max_followings: Maximum number of followings to fetch (None = all)
            page_size: Number of results per page (20-200)

        Returns:
            List of following user objects
        """
        all_followings = []
        cursor = ""
        page_num = 0

        while True:
            page_num += 1

            # Check if we've reached the limit
            if max_followings and len(all_followings) >= max_followings:
                break

            # Get page
            response = self.get_followings_page(username, cursor=cursor, page_size=page_size)

            followings = response.get('followings', [])
            all_followings.extend(followings)

            # Check if there's more
            has_next = response.get('has_next_page', False)
            if not has_next:
                break

            cursor = response.get('next_cursor', '')
            if not cursor:
                break

        # Trim to max_followings if specified
        if max_followings:
            all_followings = all_followings[:max_followings]

        return all_followings

    def extract_usernames(self, followings: List[Dict]) -> List[str]:
        """
        Extract usernames from followings list.

        Args:
            followings: List of following user objects

        Returns:
            List of usernames
        """
        usernames = []
        for following in followings:
            username = following.get('userName')
            if username:
                usernames.append(username)
        return usernames


def load_config(config_path: str = 'config.json') -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def load_existing_accounts(csv_path: str = 'accounts.csv') -> Set[str]:
    """
    Load existing accounts from CSV file.

    Returns:
        Set of existing usernames
    """
    if not Path(csv_path).exists():
        return set()

    existing = set()
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip empty rows and comments
                if not row or not row[0] or row[0].startswith('#'):
                    continue

                username = row[0].strip()
                if username and username != 'username':
                    username = username.lstrip('@')
                    existing.add(username)
    except Exception as e:
        print(f"Warning: Could not read {csv_path}: {e}")
        return set()

    return existing


def load_small_accounts(csv_path: str = 'small_accounts.csv') -> Set[str]:
    """
    Load small accounts from CSV file.

    Returns:
        Set of small account usernames
    """
    if not Path(csv_path).exists():
        return set()

    small = set()
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip empty rows and comments
                if not row or not row[0] or row[0].startswith('#'):
                    continue

                username = row[0].strip()
                if username and username != 'username':
                    username = username.lstrip('@')
                    small.add(username)
    except Exception as e:
        print(f"Warning: Could not read {csv_path}: {e}")
        return set()

    return small


def save_accounts_to_csv(accounts: Set[str], csv_path: str = 'accounts.csv'):
    """
    Save accounts to CSV file.

    Args:
        accounts: Set of usernames to save
        csv_path: Path to accounts.csv
    """
    sorted_accounts = sorted(accounts)

    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['username'])

        # Write usernames
        for username in sorted_accounts:
            writer.writerow([username])


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Get followings from a Twitter user and add to accounts.csv'
    )
    parser.add_argument(
        '--user',
        type=str,
        required=True,
        help='Twitter username to get followings from'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=None,
        help='Maximum number of followings to fetch (default: all)'
    )
    parser.add_argument(
        '--page-size',
        type=int,
        default=200,
        help='Number of followings per page (20-200, default: 200)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Get User Followings")
    print("=" * 70)
    print()

    # Load configuration
    try:
        config = load_config()
        api_key = config['api']['key']
        rate_limit = config['api'].get('rate_limit_seconds', 0.05)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return

    # Initialize client
    client = FollowingsClient(api_key, min_delay=rate_limit)

    # Get username
    username = args.user.lstrip('@')

    print(f"Target user: @{username}")
    if args.max:
        print(f"Max followings to fetch: {args.max}")
    else:
        print(f"Fetching all followings")
    print(f"Rate limit: {rate_limit}s between calls")
    print()

    # Load existing accounts
    print("Loading existing accounts...")
    existing_accounts = load_existing_accounts('accounts.csv')
    print(f"  ✓ Loaded {len(existing_accounts)} existing accounts")

    # Load small accounts
    small_accounts = load_small_accounts('small_accounts.csv')
    if small_accounts:
        print(f"  ✓ Loaded {len(small_accounts)} small accounts (will exclude)")

    print()

    # Fetch followings
    print(f"Fetching followings for @{username}...")
    print("─" * 70)

    try:
        followings = client.get_all_followings(
            username,
            max_followings=args.max,
            page_size=args.page_size
        )

        print(f"✓ Fetched {len(followings)} followings")
        print()

        # Extract usernames
        usernames = client.extract_usernames(followings)
        print(f"Extracted {len(usernames)} usernames")

        # Filter out existing and small accounts
        new_accounts = set(usernames) - existing_accounts - small_accounts
        already_exist = set(usernames) & existing_accounts
        are_small = set(usernames) & small_accounts

        print()
        print("─" * 70)
        print("Filtering results:")
        print(f"  Already in accounts.csv:     {len(already_exist)}")
        print(f"  In small_accounts.csv:       {len(are_small)}")
        print(f"  New accounts to add:         {len(new_accounts)}")
        print("─" * 70)
        print()

        if new_accounts:
            # Combine with existing
            combined_accounts = existing_accounts | new_accounts

            # Save to CSV
            print(f"Adding {len(new_accounts)} new accounts to accounts.csv...")
            save_accounts_to_csv(combined_accounts, 'accounts.csv')
            print(f"✓ Saved {len(combined_accounts)} total accounts to accounts.csv")
            print()

            # Show sample
            print("Sample of new accounts added:")
            for i, acc in enumerate(sorted(new_accounts)[:20], 1):
                print(f"  {i}. @{acc}")

            if len(new_accounts) > 20:
                print(f"  ... and {len(new_accounts) - 20} more")

        else:
            print("ℹ️  No new accounts to add")
            print("All followings are already in accounts.csv or small_accounts.csv")

        print()
        print("=" * 70)
        print("✅ Done!")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
