# Twitter/X Early Response System

## Project Goal
Monitor specific Twitter/X accounts and get notified when they post something recent (under 10 minutes old), enabling quick responses to be one of the first to reply.

## System Architecture

### Components

1. **Post Monitor Service** (`post_monitor.py`)
   - Launches its own headless browser using Playwright
   - Checks monitored accounts every 2 minutes (configurable)
   - Parses post timestamps (e.g., "5m", "2h")
   - Only notifies for posts under threshold (10 minutes by default)
   - No state tracking needed - timestamp-based approach
   - Error handling with automatic retry
   - Sends startup/shutdown notifications

2. **Notification System** (`notifier.py`)
   - Telegram bot integration for instant notifications
   - Async message sending with error handling
   - Post preview with URL and timestamp
   - Utility functions to get chat ID
   - Test mode for verification

3. **Data Storage**
   - `accounts.txt` - Simple list of accounts to monitor (one per line)
   - `config.json` - System configuration (Telegram, monitoring settings)

4. **Optional Tools**
   - `account_scraper.py` - Legacy tool to scrape followers (optional)
   - `chrome_test.py` - Legacy Chrome connection tester (optional)

## Implementation Details

### Browser Launch
- Launches Playwright's own Chromium browser
- Uses persistent context to save login session
- First run: Manually log in, session saved in `browser_data/`
- Future runs: Automatically uses saved login
- Headless by default (configurable)
- Custom user agent for reliability

### Monitoring Logic
- Navigates to each account's profile page
- Finds the most recent post
- Extracts timestamp from time element (e.g., "5m", "2h")
- Parses relative timestamps to minutes
- Only notifies if post is under threshold (default 10 minutes)
- No state tracking - timestamp comparison is stateless

### Timestamp Parsing
- Supports: seconds (s), minutes (m), hours (h), days (d)
- Example: "5m" → 5 minutes, "2h" → 120 minutes
- Falls back gracefully if timestamp can't be parsed
- Skips posts with full dates (older posts)

### Rate Limiting Strategy
- 2-minute intervals between check cycles (configurable)
- 2-second delay between individual account checks
- Graceful error handling on timeouts
- Page load timeout of 20 seconds

## Compliance & Safety

- ✅ Uses read-only operations (no automated posting)
- ✅ Respects rate limits with conservative timing
- ✅ No account association with scraping (uses your session)
- ✅ User manually posts replies (not automated)
- ✅ Monitors public information only
- ✅ Scrapes followers, not suggested accounts
- ✅ Limited to 100 accounts by default

## Technical Stack

- Python 3.12+
- Playwright 1.40+ for browser automation
- python-telegram-bot 20.0+ for notifications
- requests 2.31+ for HTTP
- CSV for account storage
- JSON for state management

## Usage Flow

1. **Setup**
   - Create Telegram bot via @BotFather
   - Configure `config.json` with bot token and settings
   - Get chat ID using `notifier.py --get-chat-id`
   - Add usernames to `accounts.txt`

2. **Monitor**
   - Run `post_monitor.py`
   - Script launches its own browser
   - Checks all accounts every 2 minutes
   - Receive Telegram notifications for recent posts only
   - Manually reply to posts

3. **Stop**
   - Ctrl+C to stop monitor
   - No state to save (stateless design)
   - Resume anytime

## Configuration

```json
{
  "telegram": {
    "bot_token": "...",
    "chat_id": "..."
  },
  "monitoring": {
    "check_interval_seconds": 120,
    "recent_post_minutes": 10,
    "headless": true
  }
}
```

### `accounts.txt` Format
```
# One username per line
# Lines starting with # are comments
vickyjadex
elonmusk
```

## Advantages of New Approach

✅ **Simpler Setup** - No Chrome debugging setup needed
✅ **No Login Required** - Reads public information only
✅ **Smarter Notifications** - Only alerts for recent posts (< 10 min)
✅ **No State Management** - Timestamp-based, no state files
✅ **More Reliable** - Doesn't depend on external Chrome instance
✅ **Fewer Notifications** - Filters out old posts automatically

## Future Enhancements

- [ ] Advanced filtering (keywords, post types, media)
- [ ] Priority accounts with different thresholds
- [ ] Historical post timing analysis
- [ ] Performance optimization (parallel checks)
- [ ] Web dashboard for monitoring
- [ ] Multiple notification channels (Discord, SMS)
- [ ] Support for Twitter Lists
- [ ] Post engagement metrics tracking
- [ ] Dynamic threshold adjustment based on account activity
