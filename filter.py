#!/usr/bin/env python3
"""
Filter out small accounts that the API doesn't have data for.

Verification System:
- Checks accounts.csv for unverified accounts
- Skips accounts already in verified_accounts.csv (saves API calls!)
- For new accounts, checks for tweets in the past 24 hours
- Accounts WITH tweets → Added to verified_accounts.csv
- Accounts WITHOUT tweets → Moved to small_accounts.csv

Only checks each account ONCE, saving API calls on subsequent runs.
"""

import csv
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from twitterapi_io.advanced_monitor import AdvancedTwitterMonitor, load_config


# ANSI Color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def load_accounts_list(csv_path: str = 'accounts.csv') -> list[str]:
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


def load_small_accounts(csv_path: str = 'small_accounts.csv') -> set[str]:
    """Load small accounts from CSV file."""
    accounts = set()

    if not Path(csv_path).exists():
        return accounts

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    username = row[0].strip()
                    if username and username != 'username':
                        username = username.lstrip('@')
                        accounts.add(username)
        return accounts

    except Exception as e:
        print(f"Warning: Could not load {csv_path}: {e}")
        return accounts


def load_verified_accounts(csv_path: str = 'verified_accounts.csv') -> set[str]:
    """Load verified accounts from CSV file."""
    accounts = set()

    if not Path(csv_path).exists():
        return accounts

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    username = row[0].strip()
                    if username and username != 'username':
                        username = username.lstrip('@')
                        accounts.add(username)
        return accounts

    except Exception as e:
        print(f"Warning: Could not load {csv_path}: {e}")
        return accounts


def save_accounts_list(accounts: list[str], csv_path: str = 'accounts.csv'):
    """Save accounts to CSV file."""
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username'])
        for username in accounts:
            writer.writerow([username])


def append_to_small_accounts(username: str, csv_path: str = 'small_accounts.csv'):
    """Append an account to small_accounts.csv."""
    file_exists = Path(csv_path).exists()

    with open(csv_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['username'])
        writer.writerow([username])


def append_to_verified_accounts(username: str, csv_path: str = 'verified_accounts.csv'):
    """Append an account to verified_accounts.csv."""
    file_exists = Path(csv_path).exists()

    with open(csv_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['username'])
        writer.writerow([username])


def check_account_has_tweets(
    monitor: AdvancedTwitterMonitor,
    username: str,
    hours: int = 24
) -> bool:
    """
    Check if an account has any tweets in the past N hours.

    Args:
        monitor: AdvancedTwitterMonitor instance
        username: Username to check
        hours: How many hours back to check

    Returns:
        True if tweets found, False otherwise
    """
    until_time = datetime.now(timezone.utc)
    since_time = until_time - timedelta(hours=hours)

    try:
        query = monitor.build_query(username, since_time, until_time)
        response = monitor.search_tweets(query)
        tweets = response.get('tweets', [])

        return len(tweets) > 0

    except Exception as e:
        print(f"    Error checking @{username}: {e}")
        # If there's an error, assume it's a valid account (don't filter it out)
        return True


def main():
    """Main filtering process."""
    print("=" * 70)
    print("Account Filter - Remove Small Accounts")
    print("=" * 70)
    print()

    # Load configuration
    try:
        config = load_config()
        api_key = config['api']['key']
        rate_limit = config['api'].get('rate_limit_seconds', 6.0)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return

    # Load accounts
    accounts = load_accounts_list('accounts.csv')

    if not accounts:
        print("❌ No accounts to filter")
        return

    # Load verified accounts (already checked and confirmed to have tweets)
    verified_accounts = load_verified_accounts('verified_accounts.csv')

    print(f"Loaded {len(accounts)} accounts from accounts.csv")
    if verified_accounts:
        print(f"Loaded {len(verified_accounts)} verified accounts (will skip)")
    print(f"Will check each account for tweets in past 24 hours")
    print(f"{rate_limit}-second rate limit enforced between checks")
    print()

    # Filter out already verified accounts
    accounts_to_check = [acc for acc in accounts if acc not in verified_accounts]
    already_verified = [acc for acc in accounts if acc in verified_accounts]

    if already_verified:
        print(f"Skipping {len(already_verified)} already verified accounts")
        print("─" * 70)

    if not accounts_to_check:
        print("✓ All accounts are already verified!")
        print("No API calls needed.")
        return

    print(f"Checking {len(accounts_to_check)} unverified accounts...")
    print("─" * 70)

    # Initialize monitor
    monitor = AdvancedTwitterMonitor(api_key, save_responses=False, min_delay=rate_limit)

    # Filter accounts
    active_accounts = list(already_verified)  # Start with already verified
    small_accounts = []
    newly_verified = []

    for i, username in enumerate(accounts_to_check, 1):
        print(f"[{i}/{len(accounts_to_check)}] Checking @{username}...", end=" ")

        has_tweets = check_account_has_tweets(monitor, username, hours=24)

        if has_tweets:
            print(f"{Colors.GREEN}✓ Has tweets (verified){Colors.RESET}")
            active_accounts.append(username)
            newly_verified.append(username)
            append_to_verified_accounts(username)
        else:
            print(f"{Colors.YELLOW}✗ No tweets found (filtering out){Colors.RESET}")
            small_accounts.append(username)
            append_to_small_accounts(username)

    print("─" * 70)
    print()

    # Summary
    print("=" * 70)
    print("FILTERING COMPLETE")
    print("=" * 70)
    print(f"Already verified (skipped):      {len(already_verified)}")
    print(f"Newly verified (has tweets):     {len(newly_verified)}")
    print(f"Small accounts (no tweets):      {len(small_accounts)}")
    print(f"Total active accounts:           {len(active_accounts)}")
    print()
    print(f"API calls made:                  {len(accounts_to_check)}")
    print(f"API calls saved:                 {len(already_verified)}")
    if len(accounts) > 0:
        savings_percent = (len(already_verified) / len(accounts)) * 100
        print(f"Savings:                         {savings_percent:.1f}%")
    print()

    if newly_verified:
        print(f"Newly verified accounts added to verified_accounts.csv:")
        for username in newly_verified:
            print(f"  {Colors.GREEN}✓ @{username}{Colors.RESET}")
        print()

    if small_accounts:
        print(f"Small accounts moved to small_accounts.csv:")
        for username in small_accounts:
            print(f"  {Colors.YELLOW}✗ @{username}{Colors.RESET}")
        print()

    # Save updated accounts.csv
    if active_accounts != accounts:
        print(f"Updating accounts.csv with {len(active_accounts)} active accounts...")
        save_accounts_list(active_accounts, 'accounts.csv')
        print("✓ accounts.csv updated")
    else:
        print("✓ No changes needed to accounts.csv")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
