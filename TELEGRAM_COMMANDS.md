# Telegram Interactive Commands

## Overview

You can now control the monitor directly from your Telegram chat! Remove unwanted accounts on-the-fly without stopping the monitor.

## How It Works

### 1. **Notification Format**

When you receive a notification, it now includes a removal hint:

```
🚨 New post from @username

[Post preview...]

View Post

Reply with 'x' to remove @username from monitoring
```

### 2. **Remove Account Command**

Simply reply with `x` in your Telegram chat to remove the last notified account.

**Example:**
```
Bot: 🚨 New post from @annoying_account
You: x
Bot: ✅ Removed @annoying_account from monitoring

     Added to small_accounts.csv
```

### 3. **Remove Specific Account**

You can also remove a specific account by typing:
```
x @username
```

**Example:**
```
You: x @some_account
Bot: ✅ Removed @some_account from monitoring

     Added to small_accounts.csv
```

## What Happens When You Remove an Account

1. **Removed from accounts.csv** - Won't be monitored anymore
2. **Added to small_accounts.csv** - Marked as unwanted
3. **Skipped immediately** - If it's currently being checked, it's skipped
4. **Confirmation sent** - You get a Telegram confirmation

## Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `x` or `X` | Remove last notified account | Just type `x` or `X` |
| `x @username` | Remove specific account | `x @elonmusk` or `X @elonmusk` |

**Note:** Commands are case-insensitive. Both `x` and `X` work the same way.

## Workflow Example

**Scenario:** Monitor finds an unwanted post

```
Monitor: [1/91] Checking @unwanted_account...
Monitor:   🚨 RECENT POST! Posted 5.2 minutes ago
Monitor:   ✓ Telegram notification sent

Telegram Bot: 🚨 New post from @unwanted_account
              [Post preview]
              View Post
              Reply with 'x' to remove @unwanted_account from monitoring

You: x

Telegram Bot: ✅ Removed @unwanted_account from monitoring
              Added to small_accounts.csv

Monitor:   ℹ️  Removed @unwanted_account from monitoring via Telegram command
```

## Features

### ✅ **Real-time Removal**
- Account is removed immediately
- No need to restart the monitor
- Takes effect in the current cycle

### ✅ **Smart Tracking**
- Bot remembers the last account it notified you about
- Just type `x` - no need to type the username

### ✅ **Persistent**
- Changes are saved to CSV files
- Won't be re-added by account_scraper.py (checks small_accounts.csv)
- Permanent removal unless you manually edit the files

### ✅ **Safe**
- Only removes from your monitoring list
- Doesn't affect the actual Twitter account
- Reversible by manually editing CSV files

## Error Handling

### Account Not Found
```
You: x @nonexistent
Bot: ❌ Failed to remove @nonexistent
     Account not found in accounts.csv
```

### No Recent Notification
```
You: x
Bot: ⚠️ No recent notification to remove
```

## Behind the Scenes

### Command Checking
- Monitor checks for commands **before each account check**
- Uses Telegram's `getUpdates` API
- Processes commands in real-time
- No polling delay

### State Management
- Tracks `last_notified_account` in memory
- Resets after successful removal
- Survives until next notification

### File Updates
1. Reads `accounts.csv`
2. Removes the account
3. Writes updated `accounts.csv`
4. Appends to `small_accounts.csv`
5. Sends confirmation

## Tips

### Quick Removal
As soon as you see an unwanted notification, just type `x` - no need to copy the username!

### Bulk Removal
Remove multiple accounts in sequence:
```
You: x @account1
Bot: ✅ Removed...

You: x @account2
Bot: ✅ Removed...

You: x @account3
Bot: ✅ Removed...
```

### Check Removed Accounts
View `small_accounts.csv` to see all removed accounts:
```bash
cat small_accounts.csv
```

### Restore an Account
1. Open `small_accounts.csv`
2. Remove the username
3. Open `accounts.csv`
4. Add the username back

## Security

- Commands only work from your configured `chat_id`
- Other users can't control your monitor
- Commands are processed securely through Telegram's API

## Troubleshooting

### Bot Not Responding to Commands
- Check bot token in `config.json`
- Make sure you're messaging the correct bot
- Verify chat_id matches your Telegram ID

### Account Not Removed
- Check if account exists in `accounts.csv`
- Ensure proper spelling (case doesn't matter)
- Check for `@` prefix (optional)

### Want to Disable This Feature
The monitor will work fine even if you never use commands. Just ignore the "Reply with 'x'" messages.

## Example Session

```
# Start monitoring
$ python post_monitor.py

======================================================================
Twitter/X Recent Post Monitor - TwitterAPI.io
======================================================================
...
Press Ctrl+C to stop
======================================================================

CYCLE #1
======================================================================

[1/91] Checking @account1...
  None found in the past 180 minutes

[2/91] Checking @spam_account...
  🚨 RECENT POST! Posted 12.3 minutes ago
  URL: https://x.com/spam_account/status/...
  ✓ Telegram notification sent

# You receive notification in Telegram
# You type: x

  ℹ️  Removed @spam_account from monitoring via Telegram command

[3/91] Checking @account3...
  None found in the past 180 minutes
```

Now `@spam_account` is permanently removed and won't appear in future cycles!
