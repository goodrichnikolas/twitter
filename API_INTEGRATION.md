# API Integration Guide

## Overview

The system has been updated to use a paid API service instead of Playwright browser automation.

## What Was Removed

### Dependencies
- ❌ `playwright` - No longer needed
- ❌ Browser automation code
- ❌ Login/session management
- ❌ `browser_data/` folder
- ❌ Headless mode configuration

### Files Removed
- `LOGIN_SETUP.md` - No longer needed for API approach

### Code Changes
- `post_monitor.py` - Completely rewritten for API calls
- `requirements.txt` - Removed playwright dependency
- All documentation updated

## What You Need

### 1. API Service

You'll need to choose and sign up for a Twitter/X API service. Some options:

**Official Twitter API (X API)**
- Free tier: Very limited
- Basic tier: $100/month
- Pro tier: More expensive
- https://developer.twitter.com/en/products/twitter-api

**Third-Party API Services**
- RapidAPI Twitter alternatives
- Apify Twitter scrapers
- Other API aggregators

### 2. Configuration

Add your API key to `config.json`:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "api": {
    "key": "YOUR_API_KEY_HERE",
    "base_url": "https://api.example.com/v1"  // Optional
  },
  "monitoring": {
    "check_interval_seconds": 120,
    "recent_post_minutes": 10
  }
}
```

## Implementation Required

The following functions in `post_monitor.py` need to be implemented:

### 1. `get_user_tweets_api(username, api_key)`

This function should make an API call to fetch recent tweets for a user.

**Example implementation:**

```python
def get_user_tweets_api(username, api_key):
    """Fetch recent tweets for a user using API"""
    import requests

    # Example for a generic API
    response = requests.get(
        f"https://api.example.com/v1/users/{username}/tweets",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"count": 10}  # Get last 10 tweets
    )

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        raise Exception("Rate limit exceeded")
    else:
        raise Exception(f"API error: {response.status_code}")
```

### 2. `check_account_recent_post(username, api_key, recent_minutes)`

This function should parse the API response and check for recent posts.

**Example implementation:**

```python
def check_account_recent_post(username, api_key, recent_minutes=10):
    """Check if account has recent posts"""
    from datetime import datetime, timezone

    try:
        tweets = get_user_tweets_api(username, api_key)

        if not tweets or len(tweets) == 0:
            return None

        # Get the latest tweet
        latest_tweet = tweets[0]

        # Parse timestamp (format depends on your API)
        # Example for ISO 8601 timestamp
        tweet_time = datetime.fromisoformat(
            latest_tweet['created_at'].replace('Z', '+00:00')
        )

        # Calculate minutes ago
        now = datetime.now(timezone.utc)
        time_diff = now - tweet_time
        minutes_ago = time_diff.total_seconds() / 60

        # Check if recent enough
        if minutes_ago <= recent_minutes:
            return {
                'username': username,
                'url': latest_tweet['url'],  # or construct it
                'text': latest_tweet['text'],
                'timestamp': latest_tweet['created_at'],
                'minutes_ago': minutes_ago
            }

        return None

    except Exception as e:
        print(f"Error checking @{username}: {e}")
        return None
```

## API Response Examples

Different APIs return data in different formats. Here are some common structures:

### Twitter Official API v2

```json
{
  "data": [
    {
      "id": "1234567890",
      "text": "This is a tweet",
      "created_at": "2025-01-15T10:30:00.000Z",
      "author_id": "123456"
    }
  ]
}
```

### Generic API

```json
{
  "tweets": [
    {
      "tweet_id": "1234567890",
      "content": "This is a tweet",
      "timestamp": "2025-01-15T10:30:00Z",
      "username": "someuser",
      "url": "https://x.com/someuser/status/1234567890"
    }
  ]
}
```

## Rate Limiting

Most APIs have rate limits. Handle them properly:

```python
import time

def get_user_tweets_api(username, api_key):
    """Fetch tweets with rate limit handling"""
    import requests

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"https://api.example.com/v1/users/{username}/tweets",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get('Retry-After', retry_delay))
                print(f"  Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            else:
                raise Exception(f"API error: {response.status_code}")

        except requests.Timeout:
            print(f"  Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise

    raise Exception("Max retries exceeded")
```

## Testing

Before running the full monitor, test your API integration:

```python
# test_api.py
from post_monitor import get_user_tweets_api, check_account_recent_post

# Test fetching tweets
username = "elonmusk"
api_key = "your-api-key"

print(f"Testing API for @{username}...")
tweets = get_user_tweets_api(username, api_key)
print(f"Got {len(tweets)} tweets")

# Test checking for recent posts
recent = check_account_recent_post(username, api_key, recent_minutes=60)
if recent:
    print(f"Recent post found: {recent['minutes_ago']:.1f} minutes ago")
else:
    print("No recent posts")
```

Run with:
```bash
python test_api.py
```

## Cost Estimation

Estimate your API costs:

- **Accounts monitored**: 21
- **Check interval**: 2 minutes
- **Checks per hour**: 30
- **API calls per hour**: 21 × 30 = 630
- **API calls per day**: 630 × 24 = 15,120
- **API calls per month**: ~453,600

If your API charges $0.0001 per call:
- **Monthly cost**: $45.36

Adjust `check_interval_seconds` to reduce costs:
- 5 minutes: ~181,440 calls/month → $18.14
- 10 minutes: ~90,720 calls/month → $9.07

## Next Steps

1. **Choose API service** - Sign up and get API key
2. **Implement functions** - Fill in `get_user_tweets_api()` and parsing logic
3. **Test** - Run test_api.py to verify it works
4. **Configure** - Add API key to config.json
5. **Run** - Start `python post_monitor.py`

## Tips

- Start with a small number of accounts to test
- Monitor your API usage dashboard
- Set up billing alerts
- Consider caching to reduce API calls
- Handle errors gracefully (API downtime, rate limits)
- Log all API responses for debugging

## Example: RapidAPI Integration

If using RapidAPI:

```python
def get_user_tweets_api(username, api_key):
    """Fetch tweets using RapidAPI"""
    import requests

    url = "https://twitter154.p.rapidapi.com/user/tweets"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }

    params = {
        "username": username,
        "limit": "10"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    else:
        raise Exception(f"API error: {response.status_code}")
```

## Support

Once you've chosen your API service, I can help you implement the specific integration for that service's response format.
