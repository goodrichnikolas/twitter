# Testing Guide

## Integration Tests

Comprehensive tests to verify the Twitter monitoring system is working correctly.

### What Gets Tested

#### 1. Advanced Search API Tests
- ✅ **Find Recent Tweet** - Searches for @elonmusk's most recent tweet in last 24 hours
- ✅ **Query Format** - Validates the query syntax is correct
- ✅ **Empty Results** - Tests handling of queries with no tweets

#### 2. Telegram Tests
- ✅ **Connection** - Verifies bot token and chat ID are valid
- ✅ **Send Test Message** - Sends an actual test message to your Telegram
- ✅ **Formatted Notification** - Tests the new post notification format

#### 3. End-to-End Test
- ✅ **Full Monitoring Cycle** - Complete workflow: search → find tweet → send notification

## Running Tests

### Option 1: With pytest (Recommended)

```bash
# Install pytest if needed
pip install pytest

# Run all tests with verbose output
pytest test_integration.py -v -s

# Run specific test class
pytest test_integration.py::TestAdvancedSearch -v -s

# Run specific test
pytest test_integration.py::TestAdvancedSearch::test_find_recent_elonmusk_tweet -v -s
```

### Option 2: Manual Run

```bash
python test_integration.py --manual
```

This runs all tests sequentially without pytest.

## Expected Output

### Successful Test Run:

```
======================================================================
TWITTER MONITORING SYSTEM - INTEGRATION TESTS
======================================================================

======================================================================
TEST: Finding recent tweet from @elonmusk
======================================================================

Searching for tweets from @elonmusk
Time range: 2025-11-12 13:30:00 to 2025-11-13 13:30:00 UTC
Query: from:elonmusk since:2025-11-12_13:30:00_UTC until:2025-11-13_13:30:00_UTC include:nativeretweets

Found 127 tweet(s)

Most recent tweet:
  ID: 1989036267145949424
  Text: Example tweet text...
  Created: Thu Nov 13 18:22:55 +0000 2025
  URL: https://x.com/elonmusk/status/1989036267145949424

✓ Test passed: Successfully found recent tweet from @elonmusk
======================================================================

...

======================================================================
TEST: Send test message to Telegram
======================================================================

Sending test message to Telegram...
Message: 🧪 Test Message from Integration Tests...

✓ Test passed: Message sent to Telegram
Check your Telegram to confirm you received it!
======================================================================

...

======================================================================
✅ ALL TESTS PASSED!
======================================================================
```

## Test Details

### Test 1: Find Recent Tweet

**What it does:**
- Searches @elonmusk for tweets in last 24 hours
- Verifies at least one tweet is found
- Checks tweet has correct structure (id, text, author, etc.)

**Why @elonmusk:**
- Tweets very frequently (high success rate)
- Public account (no login issues)
- Good test of API functionality

**Success criteria:**
- Returns at least 1 tweet
- Tweet has all required fields
- Author username matches

### Test 2: Query Format

**What it does:**
- Generates a query with specific dates
- Validates format matches expected pattern

**Success criteria:**
- Contains `from:username`
- Date format: `YYYY-MM-DD_HH:MM:SS_UTC`
- Includes retweets flag if enabled

### Test 3: Empty Results

**What it does:**
- Queries a narrow time window with no tweets
- Verifies empty results are handled correctly

**Success criteria:**
- Returns empty list (not error)
- No crashes or exceptions

### Test 4: Telegram Connection

**What it does:**
- Verifies bot token and chat ID are set
- Checks bot instance is created

**Success criteria:**
- Bot object exists
- Credentials are present

### Test 5: Send Test Message

**What it does:**
- Sends real test message to your Telegram
- Uses HTML formatting

**Success criteria:**
- Message sends without error
- Returns success = True

**Note:** Check your Telegram to confirm you received it!

### Test 6: Formatted Notification

**What it does:**
- Sends a mock "new post" notification
- Tests the formatted message style

**Success criteria:**
- Message sends successfully
- Proper formatting with username, URL, preview

**Note:** This will appear in Telegram as if a real post was detected!

### Test 7: Full Monitoring Cycle

**What it does:**
- Searches for tweets from @elonmusk (last hour)
- If found, sends notification via Telegram
- Complete end-to-end workflow

**Success criteria:**
- Search executes without errors
- If tweets found, notification sends successfully

## Troubleshooting

### Test Fails: "No tweets found from @elonmusk"

**Possible causes:**
- Rate limited (wait 6 seconds between tests)
- Time window too narrow
- API key issue

**Solution:**
```bash
# Run individual test with longer wait
pytest test_integration.py::TestAdvancedSearch::test_find_recent_elonmusk_tweet -v -s
```

### Test Fails: "Telegram message failed"

**Possible causes:**
- Invalid bot token
- Invalid chat ID
- Network issues

**Solution:**
1. Verify `config.json` has correct credentials
2. Test bot manually: `python notifier.py`
3. Make sure you messaged your bot first

### Rate Limit Errors

Tests automatically enforce 6-second delays between API calls. If you still hit rate limits:

```bash
# Run tests one at a time
pytest test_integration.py::TestAdvancedSearch::test_find_recent_elonmusk_tweet -v -s
# Wait 10 seconds
pytest test_integration.py::TestTelegram::test_send_test_message -v -s
```

### JSON Response Inspection

All API responses are saved to `jsons/` folder. If a test fails, check:

```bash
ls -lt jsons/ | head -5
cat jsons/advanced_search_XXXXX_TIMESTAMP.json
```

## Adding More Tests

To add your own tests:

```python
class TestCustom:
    """Your custom tests"""

    def test_your_account(self, monitor):
        """Test with your own account"""
        username = "your_username"

        until_time = datetime.now(timezone.utc)
        since_time = until_time - timedelta(hours=1)

        query = monitor.build_query(username, since_time, until_time)
        response = monitor.search_tweets(query)

        tweets = response.get('tweets', [])
        assert len(tweets) > 0, f"Should find tweets from @{username}"
```

Then run:
```bash
pytest test_integration.py::TestCustom::test_your_account -v -s
```

## CI/CD Integration

To run in automated pipelines:

```bash
# Exit with error code if any test fails
pytest test_integration.py -v --tb=short

# Generate XML report
pytest test_integration.py --junit-xml=test-results.xml

# Run only non-Telegram tests (for CI without credentials)
pytest test_integration.py -v -k "not telegram"
```

## Summary

Run this before deploying to verify:
- ✅ API key works
- ✅ Advanced Search finds tweets
- ✅ Telegram credentials valid
- ✅ Notifications send correctly
- ✅ Full monitoring cycle works

**Quick check:**
```bash
python test_integration.py --manual
```

Should take ~30 seconds and send 2-3 test messages to Telegram.
