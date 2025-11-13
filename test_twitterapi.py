#!/usr/bin/env python3
"""
Test script for TwitterAPI.io integration
"""

import json
from twitterapi_io.client import TwitterAPIClient

def test_api():
    """Test the TwitterAPI.io client"""
    print("=" * 70)
    print("TwitterAPI.io Test")
    print("=" * 70)
    print()

    # Load API key from config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config['api']['key']
    except FileNotFoundError:
        print("❌ config.json not found")
        print("Please create config.json with your API key")
        return
    except KeyError:
        print("❌ API key not found in config.json")
        return

    # Initialize client
    client = TwitterAPIClient(api_key)
    print("✓ Client initialized")
    print()

    # Test with a known active account
    test_username = "elonmusk"  # Change to any account you want to test

    print(f"Testing with @{test_username}...")
    print()

    try:
        # Get latest tweet
        tweet_info = client.get_latest_tweet_info(test_username)

        if tweet_info:
            print("✓ Successfully fetched tweet!")
            print()
            print(f"Username: @{tweet_info['username']}")
            print(f"Tweet ID: {tweet_info['tweet_id']}")
            print(f"Posted: {tweet_info['minutes_ago']:.1f} minutes ago")
            print(f"URL: {tweet_info['url']}")
            print(f"Text: {tweet_info['text'][:100]}...")
            print()

            # Check if recent (within 10 minutes)
            if tweet_info['minutes_ago'] <= 10:
                print("🚨 This is a RECENT post (< 10 minutes)!")
            else:
                print("ℹ️  This post is older than 10 minutes")

        else:
            print("❌ No tweets found")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 70)
    print("Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_api()
