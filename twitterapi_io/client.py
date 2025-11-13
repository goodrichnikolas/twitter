"""
TwitterAPI.io API Client
Documentation: https://docs.twitterapi.io/
"""

import requests
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List
from pathlib import Path


class TwitterAPIClient:
    """Client for interacting with TwitterAPI.io"""

    BASE_URL = "https://api.twitterapi.io"

    def _save_response(self, username: str, response_data: Dict):
        """
        Save API response to jsons/ folder.

        Args:
            username: Twitter username
            response_data: API response data
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"jsons/{username}_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Don't fail if we can't save, just log it
            print(f"  Warning: Could not save response to {filename}: {e}")

    def __init__(self, api_key: str, save_responses: bool = True):
        """
        Initialize the TwitterAPI.io client.

        Args:
            api_key: Your TwitterAPI.io API key
            save_responses: Save API responses to jsons/ folder (default: True)
        """
        self.api_key = api_key
        self.save_responses = save_responses
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })

        # Create jsons folder if it doesn't exist
        if self.save_responses:
            Path("jsons").mkdir(exist_ok=True)

    def get_user_last_tweets(self, username: str, include_replies: bool = False) -> Dict:
        """
        Get the last tweets from a user.

        API Endpoint: GET /twitter/user/last_tweets
        Documentation: https://docs.twitterapi.io/api-reference/endpoint/get_user_last_tweets

        Args:
            username: Twitter username (without @)
            include_replies: Include replies in results (default: False)

        Returns:
            API response as dictionary

        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        endpoint = f"{self.BASE_URL}/twitter/user/last_tweets"

        params = {
            "userName": username,
            "cursor": "",
            "includeReplies": str(include_replies).lower()
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            # Get JSON response
            response_data = response.json()

            # Save response to file
            if self.save_responses:
                self._save_response(username, response_data)

            return response_data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Check for Retry-After header
                retry_after = e.response.headers.get('Retry-After', '60')
                raise Exception(f"Rate limit exceeded. Retry after {retry_after}s") from e
            elif e.response.status_code == 401:
                raise Exception("Invalid API key") from e
            elif e.response.status_code == 404:
                raise Exception(f"User @{username} not found") from e
            else:
                raise Exception(f"API error: {e.response.status_code}") from e

        except requests.exceptions.Timeout:
            raise Exception("API request timed out")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}") from e

    def get_latest_tweet_info(self, username: str) -> Optional[Dict]:
        """
        Get information about the latest tweet from a user.

        Args:
            username: Twitter username (without @)

        Returns:
            Dictionary with tweet info, or None if no tweets found
            {
                'username': str,
                'tweet_id': str,
                'text': str,
                'created_at': str,
                'url': str,
                'minutes_ago': float
            }
        """
        try:
            response = self.get_user_last_tweets(username)

            # Get data object
            data = response.get('data', {})

            # Check if user is unavailable
            if isinstance(data, dict) and data.get('unavailable'):
                reason = data.get('unavailableReason', 'Unknown')
                print(f"  User @{username} unavailable: {reason}")
                return None

            # Parse response - tweets are in data.tweets array
            tweets = data.get('tweets', [])

            if not tweets:
                return None

            latest_tweet = tweets[0]

            # Parse timestamp (format: "Tue Dec 10 07:00:30 +0000 2024")
            created_at = latest_tweet.get('createdAt')
            if not created_at:
                return None

            # Parse Twitter date format to datetime
            from datetime import datetime
            tweet_time = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")

            # Calculate minutes ago
            now = datetime.now(timezone.utc)
            time_diff = now - tweet_time
            minutes_ago = time_diff.total_seconds() / 60

            # Get tweet ID and construct URL
            tweet_id = latest_tweet.get('id')
            tweet_url = f"https://x.com/{username}/status/{tweet_id}"

            return {
                'username': username,
                'tweet_id': tweet_id,
                'text': latest_tweet.get('text', ''),
                'created_at': created_at,
                'url': tweet_url,
                'minutes_ago': minutes_ago
            }

        except Exception as e:
            print(f"  Error fetching tweets for @{username}: {e}")
            return None

    def is_recent_post(self, username: str, minutes_threshold: int = 10) -> Optional[Dict]:
        """
        Check if user has posted within the last N minutes.

        Args:
            username: Twitter username (without @)
            minutes_threshold: Number of minutes to check (default: 10)

        Returns:
            Tweet info dict if recent post found, None otherwise
        """
        tweet_info = self.get_latest_tweet_info(username)

        if not tweet_info:
            return None

        if tweet_info['minutes_ago'] <= minutes_threshold:
            return tweet_info

        return None
