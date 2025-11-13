# Account Filtering System

## Overview

The filtering system helps you save API calls by verifying accounts once and remembering which ones have tweets.

## Files

- **accounts.csv** - All accounts you want to monitor
- **verified_accounts.csv** - Accounts confirmed to have tweets (won't be checked again)
- **small_accounts.csv** - Accounts with no tweets (excluded from monitoring)

## How It Works

### First Run
```bash
python filter.py
```

1. Loads all accounts from `accounts.csv`
2. Checks each account for tweets in past 24 hours
3. Accounts **with tweets** → Added to `verified_accounts.csv`
4. Accounts **without tweets** → Moved to `small_accounts.csv`
5. Updates `accounts.csv` to only include verified accounts

**Example:**
- Input: 100 accounts in `accounts.csv`
- Result: 80 have tweets, 20 don't
- API calls: 100 (checks all accounts)

### Second Run (Adding New Accounts)

After you add more accounts to `accounts.csv`:

```bash
python filter.py
```

1. Loads verified accounts (80 from previous run)
2. **Skips** those 80 accounts (no API calls!)
3. Only checks the 20 new accounts
4. Adds new verified accounts to `verified_accounts.csv`

**Example:**
- Added 20 new accounts to `accounts.csv` (now 100 total)
- 80 already verified (skipped)
- API calls: 20 (only checks new accounts)

### Benefits

- **First run:** 100 accounts = 100 API calls
- **Subsequent runs:** Only checks new/unverified accounts
- **Saves:** Up to 95%+ of API calls after initial verification

## Workflow

### 1. Initial Setup
```bash
# Add accounts from HTML files
python account_scraper.py

# Filter out small accounts (first time)
python filter.py
```

### 2. Add More Accounts
```bash
# Add more HTML files to x_home/ folder
python account_scraper.py

# Filter only the new accounts
python filter.py
```

### 3. Start Monitoring
```bash
# Monitor only verified accounts
python monitor_advanced.py
```

## File Contents

### verified_accounts.csv
```csv
username
elonmusk
OpenAI
Google
```
Accounts confirmed to have tweets. Filter.py will skip these.

### small_accounts.csv
```csv
username
inactive_user123
deleted_account456
```
Accounts with no tweets. Account_scraper.py won't add these again.

## Tips

- Run `filter.py` after adding new accounts via `account_scraper.py`
- First run takes longer (checks all accounts)
- Subsequent runs are much faster (only checks new accounts)
- Verified accounts are never checked again (saves API calls)
- To re-verify an account, remove it from `verified_accounts.csv`

## API Call Savings

With upgraded plan (20 calls/second):

**Before verification system:**
- 100 accounts × 0.05s = 5 seconds per cycle
- Every cycle checks all 100 accounts

**After verification system:**
- First run: 100 accounts (5 seconds)
- Adding 10 new accounts: Only 10 accounts (0.5 seconds)
- Monitoring: Only verified accounts

You only pay to verify each account **once**!
