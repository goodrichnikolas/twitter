# Monitor State Tracking System

## Overview

The monitoring system now tracks notifications to prevent duplicates and implements cooldown periods to reduce notification spam.

## Features

### 1. **Duplicate Tweet Prevention**
- Tracks every tweet ID that has been notified
- If the same tweet is found again (within the 180-minute window), it won't send a duplicate notification
- Prevents spam when cycles overlap

### 2. **Account Cooldown**
- After sending a notification for an account, that account enters a cooldown period
- Cooldown duration = `recent_post_minutes` (default: 180 minutes)
- During cooldown, the account is completely skipped (saves API calls!)
- Example: If @user1 posts at 1:00 PM and you get notified, that account won't be checked again until 4:00 PM

### 3. **State Persistence**
- All state is saved to `monitor_state.json`
- Survives script restarts
- Tracks:
  - `notified_tweets`: List of tweet IDs already notified
  - `last_notification`: Timestamp of last notification per account

## How It Works

### First Detection
```
[1/91] Checking @ItsMimiSparkles...
  🚨 RECENT POST! Posted 5.2 minutes ago
  URL: https://x.com/ItsMimiSparkles/status/1234567890
  Tweet ID: 1234567890
  ✓ Telegram notification sent
  ✓ Cooldown activated (180 minutes)
```

### Second Cycle (Same Tweet)
```
[1/91] Checking @ItsMimiSparkles...
  ℹ️  Recent post found but already notified (skipping)
  Tweet ID: 1234567890
```

### During Cooldown
```
Checking 90 accounts...
Skipping 1 accounts in cooldown
```

Account is completely skipped - no API call made!

## Benefits

### 1. **No Duplicate Notifications**
- Same tweet will never trigger multiple notifications
- Even if you restart the monitor, it remembers

### 2. **Reduced API Calls**
- Accounts in cooldown are skipped entirely
- Example: If 20 accounts have recently posted, those 20 are skipped each cycle
- With 180-minute cooldown and 5-minute cycles, accounts are checked ~1/36th as often

### 3. **Smarter Monitoring**
- Focuses on accounts that haven't posted recently
- Cycles complete faster when many accounts are in cooldown

## Configuration

Cooldown period is automatically set to match `recent_post_minutes` in `config.json`:

```json
{
  "monitoring": {
    "recent_post_minutes": 180
  }
}
```

- **180 minutes** = 3-hour cooldown after each notification
- Adjust this value to change both:
  - How far back to search for tweets
  - How long to wait before checking the account again

## State File

The state is stored in `monitor_state.json`:

```json
{
  "notified_tweets": [
    "1234567890",
    "9876543210",
    ...
  ],
  "last_notification": {
    "ItsMimiSparkles": 1699900000.0,
    "elonmusk": 1699910000.0,
    ...
  }
}
```

### Maintenance

The state file automatically manages itself:
- Keeps the last 10,000 tweet IDs (configurable)
- Old tweets are automatically removed
- No manual cleanup needed

To view state statistics:
```bash
python monitor_state.py
```

Output:
```
Monitor State Statistics
======================================================================
total_tweets_tracked: 45
accounts_with_notifications: 12
accounts_in_cooldown: 3

Accounts in cooldown:
  @ItsMimiSparkles: 145.2 minutes remaining
  @user2: 32.5 minutes remaining
  @user3: 89.1 minutes remaining
```

## Example Scenarios

### Scenario 1: Fast Cycles
- Config: `check_interval_seconds: 60`, `recent_post_minutes: 180`
- Cycle completes every 2-5 minutes
- Account posts at 1:00 PM
- Notification sent at 1:02 PM
- Account skipped until 4:02 PM (180 minutes later)
- Saves ~36 API calls per account!

### Scenario 2: Busy Period
- 50 accounts post within 1 hour
- All 50 enter cooldown
- Next cycles only check the other 41 accounts
- Cycles complete faster
- API usage drops significantly

### Scenario 3: Restart
- Monitor has been running for 2 hours
- You restart the script
- State loads from `monitor_state.json`
- All cooldowns and tracked tweets are preserved
- No duplicate notifications sent
- Monitoring continues seamlessly

## Troubleshooting

### Reset State
If you need to clear all state (start fresh):
```bash
rm monitor_state.json
```

### View Current State
```bash
python monitor_state.py
```

### Force Recheck an Account
Remove the account from `last_notification` in `monitor_state.json`:
```json
{
  "last_notification": {
    "account_to_recheck": null
  }
}
```

## Integration

Both monitoring scripts use the state system:
- `post_monitor.py` - Main monitoring script
- `twitterapi_io/monitor.py` - Alternative monitoring script

The state is shared between them - if you switch scripts, the state carries over!
