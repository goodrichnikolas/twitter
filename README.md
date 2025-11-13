# Twitter/X Early Response System

Monitor specific Twitter/X accounts and get instant Telegram notifications when they post something recent, allowing you to be one of the first to respond.

## Features

- 👀 Monitor any Twitter/X accounts (no login required)
- ⏰ Only notifies for recent posts (under 10 minutes old by default)
- 📱 Instant Telegram notifications with post previews
- 🤖 Runs its own browser (no Chrome setup needed)
- ⚡ Smart timestamp checking to reduce API calls
- 🔄 Continuous monitoring with configurable intervals

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token you receive
4. Message your new bot (just say "hi")

### 3. Configure the System

Edit `config.json`:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  },
  "monitoring": {
    "check_interval_seconds": 120,
    "recent_post_minutes": 10,
    "headless": true
  }
}
```

To get your `chat_id`:
```bash
python notifier.py --get-chat-id
```

### 4. Add Accounts to Monitor

**Option A: Manual Entry**

Create/edit `accounts.txt` and add one username per line:

```
vickyjadex
elonmusk
OpenAI
```

**Option B: Use HTML Parser (Recommended!)**

Extract accounts from saved X/Twitter HTML (avoids extension detection issues):

1. Go to [https://x.com/home](https://x.com/home)
2. Scroll down to load profiles you want to monitor
3. Press `Ctrl+S` (or `Cmd+S` on Mac) to save the page
4. Run the parser:
   ```bash
   python html_parser.py twitter_feed.html --output accounts.txt
   ```

See [HTML_PARSER_GUIDE.md](HTML_PARSER_GUIDE.md) for detailed instructions.

**Option C: Use Chrome Extension (May be detected)**

⚠️ **Note**: X/Twitter may detect and block the extension. Use Option B instead if you encounter issues.

Install the included Chrome extension to scrape accounts from your X/Twitter feed:

1. Navigate to `chrome://extensions/` in Chrome
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. Go to [https://x.com/home](https://x.com/home)
6. Click the extension icon
7. Click "Scrape Profiles"
8. Download `accounts.txt` and use it!

See [chrome-extension/README.md](chrome-extension/README.md) for detailed instructions.

### 5. Test Telegram Notifications

```bash
python notifier.py
```

You should receive a test message in Telegram.

## Usage

### First Time: Login Setup

Since X/Twitter requires login to view posts, you need to log in once:

1. Edit `config.json` and set `"headless": false`
2. Run `python post_monitor.py`
3. Browser will open - log in to X/Twitter
4. Press Enter in terminal after logging in
5. Your login is now saved!

See [LOGIN_SETUP.md](LOGIN_SETUP.md) for detailed instructions.

### Start Monitoring

```bash
python post_monitor.py
```

That's it! The script will:
- Launch its own browser (headless by default)
- Use your saved login session automatically
- Load accounts from `accounts.csv`
- Check each account every 2 minutes
- Parse the timestamp of their most recent post
- Only notify you if the post is under 10 minutes old
- Keep running until you stop it (Ctrl+C)

### How It Works

1. Every 2 minutes (configurable), the script checks each account
2. For each account, it:
   - Navigates to their profile (e.g., https://x.com/vickyjadex)
   - Finds their most recent post
   - Checks the timestamp (e.g., "5m", "2h")
3. If the post is under 10 minutes old, you get a Telegram notification
4. Otherwise, it moves to the next account

This approach minimizes notifications and API calls - you only get alerted for truly recent posts!

## Files

### Core Files
- `post_monitor.py` - Main monitoring service
- `notifier.py` - Telegram notification handler
- `config.json` - Configuration file
- `accounts.txt` - List of accounts to monitor (one per line)

### Chrome Extension
- `chrome-extension/` - Browser extension to scrape profiles from X/Twitter
  - See [chrome-extension/README.md](chrome-extension/README.md) for details

### Legacy/Optional
- `account_scraper.py` - Optional: Scrape followers from an account (legacy)
- `chrome_test.py` - Optional: Test Chrome connection (legacy)

## Configuration

### `config.json` Settings

- `check_interval_seconds` - How often to check all accounts (120 = 2 minutes)
- `recent_post_minutes` - Only notify for posts this recent (10 = last 10 minutes)
- `headless` - Run browser in background (true) or visible (false)

### `accounts.txt` Format

```
# Add one username per line
# Lines starting with # are ignored
vickyjadex
someuser
another_account
```

## Tips

- The system only notifies for recent posts (under 10 minutes by default)
- Checks happen every 2 minutes, so you might catch posts that are 2-12 minutes old
- Set `headless: false` to see the browser in action
- Add as many accounts as you want to `accounts.txt`
- The script will skip accounts that don't exist or are suspended

## Compliance

This system:
- ✅ Only reads public information (no login required)
- ✅ Respects rate limits with delays between checks
- ✅ Doesn't automate posting or engagement
- ✅ Requires manual user action to reply
- ✅ Uses standard browser automation
- ✅ Only monitors accounts you explicitly list

You remain in control and manually choose when/how to respond to posts.

## Troubleshooting

**"No accounts found"**
- Create `accounts.txt` with one username per line
- Make sure there are no typos in usernames

**"Could not parse timestamp"**
- Twitter sometimes shows full dates instead of relative times (e.g., "Jan 1")
- The script will skip these and move to the next account
- This usually happens with older posts

**Browser issues**
- Set `"headless": false` in config.json to see what's happening
- Make sure you have playwright browsers installed: `playwright install chromium`

**Telegram notifications not working**
- Run `python notifier.py` to test
- Verify your bot token and chat ID are correct
- Make sure you've messaged your bot at least once

**Too many/few notifications**
- Adjust `recent_post_minutes` in config.json
- Adjust `check_interval_seconds` to check more/less frequently