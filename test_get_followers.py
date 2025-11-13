#!/usr/bin/env python3
"""
Tests for get_followers.py - Get user followings from Twitter API

Tests the API integration and response parsing.
"""

import pytest
import json
from pathlib import Path

from get_followers import (
    FollowingsClient,
    load_config,
    load_existing_accounts,
    load_small_accounts,
    save_accounts_to_csv
)


@pytest.fixture
def config():
    """Load configuration"""
    return load_config('config.json')


@pytest.fixture
def client(config):
    """Create FollowingsClient instance"""
    api_key = config['api']['key']
    return FollowingsClient(api_key)


class TestFollowingsAPI:
    """Test the Followings API integration"""

    def test_get_single_page(self, client):
        """
        Test fetching first page of followings from a test account.
        Using @elonmusk since he has many followings.
        """
        print("\n" + "="*70)
        print("TEST: Get first page of followings")
        print("="*70)

        username = "elonmusk"

        print(f"\nFetching followings for @{username} (first page)...")

        # Get first page (cursor = "")
        response = client.get_followings_page(username, cursor="")

        print(f"\nResponse keys: {response.keys()}")
        print(f"Status: {response.get('status')}")
        print(f"Message: {response.get('message')}")
        print(f"Has next page: {response.get('has_next_page')}")

        # Check response structure
        assert 'followings' in response, "Response should have 'followings'"
        assert 'has_next_page' in response, "Response should have 'has_next_page'"
        assert 'next_cursor' in response, "Response should have 'next_cursor'"

        followings = response.get('followings', [])
        print(f"\nFound {len(followings)} followings on first page")

        assert len(followings) > 0, f"@{username} should have followings"

        # Check first following structure
        if followings:
            first = followings[0]
            print(f"\nFirst following:")
            print(f"  Username: @{first.get('userName')}")
            print(f"  Name: {first.get('name')}")
            print(f"  ID: {first.get('id')}")
            print(f"  Followers: {first.get('followersCount', 0):,}")
            print(f"  Verified: {first.get('isVerified', False)}")

            # Verify required fields
            assert 'userName' in first, "Following should have 'userName'"
            assert 'id' in first, "Following should have 'id'"
            assert 'name' in first, "Following should have 'name'"

        print("\n✓ Test passed: Successfully fetched followings page")
        print("="*70)

    def test_pagination(self, client):
        """
        Test pagination by fetching multiple pages.
        """
        print("\n" + "="*70)
        print("TEST: Pagination test (fetch 2 pages)")
        print("="*70)

        username = "elonmusk"

        print(f"\nFetching first 2 pages of followings for @{username}...")

        all_followings = []
        cursor = ""
        pages_fetched = 0
        max_pages = 2

        while pages_fetched < max_pages:
            print(f"\nFetching page {pages_fetched + 1}...")
            response = client.get_followings_page(username, cursor=cursor)

            followings = response.get('followings', [])
            all_followings.extend(followings)

            print(f"  Got {len(followings)} followings")
            print(f"  Total so far: {len(all_followings)}")

            has_next = response.get('has_next_page', False)
            print(f"  Has next page: {has_next}")

            if not has_next:
                print("  No more pages available")
                break

            cursor = response.get('next_cursor', '')
            print(f"  Next cursor: {cursor[:50]}..." if len(cursor) > 50 else f"  Next cursor: {cursor}")

            pages_fetched += 1

        print(f"\n✓ Fetched {pages_fetched} pages")
        print(f"✓ Total followings collected: {len(all_followings)}")

        assert len(all_followings) > 0, "Should collect followings"
        assert pages_fetched > 0, "Should fetch at least one page"

        print("\n✓ Test passed: Pagination works correctly")
        print("="*70)

    def test_get_all_followings_limited(self, client):
        """
        Test getting all followings with a limit.
        """
        print("\n" + "="*70)
        print("TEST: Get all followings (max 50)")
        print("="*70)

        username = "elonmusk"
        max_followings = 50

        print(f"\nFetching up to {max_followings} followings for @{username}...")

        followings = client.get_all_followings(username, max_followings=max_followings)

        print(f"\nCollected {len(followings)} followings")

        assert len(followings) > 0, "Should get followings"
        assert len(followings) <= max_followings, f"Should not exceed {max_followings}"

        # Show sample
        print("\nSample of followings:")
        for i, following in enumerate(followings[:10], 1):
            print(f"  {i}. @{following.get('userName')} - {following.get('name')}")

        if len(followings) > 10:
            print(f"  ... and {len(followings) - 10} more")

        print("\n✓ Test passed: Successfully fetched all followings")
        print("="*70)

    def test_extract_usernames(self, client):
        """
        Test extracting just usernames from followings.
        """
        print("\n" + "="*70)
        print("TEST: Extract usernames from followings")
        print("="*70)

        username = "elonmusk"

        print(f"\nFetching followings for @{username}...")

        followings = client.get_all_followings(username, max_followings=20)
        usernames = client.extract_usernames(followings)

        print(f"\nExtracted {len(usernames)} usernames")

        assert len(usernames) == len(followings), "Should extract all usernames"
        assert all(isinstance(u, str) for u in usernames), "All should be strings"

        # Show sample
        print("\nSample usernames:")
        for i, uname in enumerate(usernames[:10], 1):
            print(f"  {i}. @{uname}")

        print("\n✓ Test passed: Usernames extracted correctly")
        print("="*70)


class TestAccountManagement:
    """Test account CSV management functions"""

    def test_load_existing_accounts(self):
        """Test loading existing accounts from accounts.csv"""
        print("\n" + "="*70)
        print("TEST: Load existing accounts")
        print("="*70)

        accounts = load_existing_accounts('accounts.csv')

        print(f"\nLoaded {len(accounts)} existing accounts")

        assert isinstance(accounts, set), "Should return a set"

        if accounts:
            sample = list(accounts)[:5]
            print("\nSample accounts:")
            for acc in sample:
                print(f"  @{acc}")

        print("\n✓ Test passed: Accounts loaded")
        print("="*70)

    def test_load_small_accounts(self):
        """Test loading small accounts from small_accounts.csv"""
        print("\n" + "="*70)
        print("TEST: Load small accounts")
        print("="*70)

        small_accounts = load_small_accounts('small_accounts.csv')

        print(f"\nLoaded {len(small_accounts)} small accounts")

        assert isinstance(small_accounts, set), "Should return a set"

        if small_accounts:
            sample = list(small_accounts)[:5]
            print("\nSample small accounts:")
            for acc in sample:
                print(f"  @{acc}")

        print("\n✓ Test passed: Small accounts loaded")
        print("="*70)


class TestEndToEnd:
    """End-to-end integration test"""

    def test_full_workflow(self, client):
        """
        Test the complete workflow:
        1. Get followings from a user
        2. Extract usernames
        3. Filter out existing and small accounts
        4. Show what would be added
        """
        print("\n" + "="*70)
        print("TEST: Full workflow simulation")
        print("="*70)

        username = "elonmusk"
        max_followings = 30

        print(f"\n1. Fetching followings for @{username} (max {max_followings})...")
        followings = client.get_all_followings(username, max_followings=max_followings)
        print(f"   ✓ Found {len(followings)} followings")

        print(f"\n2. Extracting usernames...")
        usernames = client.extract_usernames(followings)
        print(f"   ✓ Extracted {len(usernames)} usernames")

        print(f"\n3. Loading existing accounts...")
        existing = load_existing_accounts('accounts.csv')
        print(f"   ✓ Loaded {len(existing)} existing accounts")

        print(f"\n4. Loading small accounts to exclude...")
        small = load_small_accounts('small_accounts.csv')
        print(f"   ✓ Loaded {len(small)} small accounts")

        print(f"\n5. Filtering...")
        new_accounts = set(usernames) - existing - small
        already_exist = set(usernames) & existing
        are_small = set(usernames) & small

        print(f"   Already in accounts.csv: {len(already_exist)}")
        print(f"   In small_accounts.csv:   {len(are_small)}")
        print(f"   New to add:              {len(new_accounts)}")

        if new_accounts:
            print(f"\n   Sample of new accounts to add:")
            for i, acc in enumerate(list(new_accounts)[:10], 1):
                print(f"     {i}. @{acc}")

        print("\n✓ Test passed: Full workflow completed")
        print("="*70)


def run_all_tests():
    """Run all tests manually (without pytest)"""
    print("\n" + "="*70)
    print("GET FOLLOWERS - INTEGRATION TESTS")
    print("="*70)

    try:
        config = load_config('config.json')
        client = FollowingsClient(config['api']['key'])

        # Test API
        test_api = TestFollowingsAPI()
        test_api.test_get_single_page(client)
        test_api.test_pagination(client)
        test_api.test_get_all_followings_limited(client)
        test_api.test_extract_usernames(client)

        # Test Account Management
        test_accounts = TestAccountManagement()
        test_accounts.test_load_existing_accounts()
        test_accounts.test_load_small_accounts()

        # Test End-to-End
        test_e2e = TestEndToEnd()
        test_e2e.test_full_workflow(client)

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
        print("  pytest test_get_followers.py -v -s")
        print("\nOr run manually:")
        print("  python test_get_followers.py --manual")
