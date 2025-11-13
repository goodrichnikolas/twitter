# Account Scraper Usage Guide

## Overview

The account scraper extracts usernames from manually saved X/Twitter HTML pages. This approach completely avoids detection issues since you're just parsing saved files offline.

## Quick Start

### 1. Save HTML from X/Twitter

1. Go to [https://x.com/home](https://x.com/home) in your browser
2. Scroll down to load profiles you want to monitor (the more you scroll, the more profiles you'll capture)
3. Press `Ctrl+S` (or `Cmd+S` on Mac) to save the page
4. Save it in the `x_home/` folder (create the folder if it doesn't exist)

### 2. Run the Scraper

```bash
python account_scraper.py
```

That's it! The script will:
- Scan the `x_home/` folder for all HTML files
- Extract usernames from each file
- Combine them with existing accounts in `accounts.csv`
- Remove duplicates automatically

## Example Session

```
======================================================================
X/Twitter Account Scraper - HTML Parser
======================================================================

📁 Found 2 HTML file(s) in x_home/
   • Home _ X.html
   • Home _ X (2).html

📊 Existing accounts in accounts.csv: 21

🔍 Processing HTML files...

  Parsing: Home _ X.html
    → Found 21 usernames
  Parsing: Home _ X (2).html
    → Found 34 usernames

──────────────────────────────────────────────────────────────────────
📈 Summary:
   Total unique usernames found in HTML files: 45
   New accounts to add: 24
   Total accounts after update: 45
──────────────────────────────────────────────────────────────────────

✅ Saved to accounts.csv

📝 Sample of new accounts added:
     @newuser1
     @newuser2
     @newuser3
     ...

======================================================================
✨ Done! Run this script anytime to update with new HTML files.

Next steps:
  • To add more accounts: Save more HTML files to x_home/ and re-run
  • To start monitoring: python post_monitor.py
======================================================================
```

## How It Works

### 1. Folder Structure

```
twitter/
├── x_home/                    # Put saved HTML files here
│   ├── Home _ X.html
│   ├── Home _ X (2).html
│   └── Home _ X (3).html
├── accounts.csv               # Generated/updated by script
└── account_scraper.py         # The script
```

### 2. Parsing Logic

The script extracts usernames using multiple methods:
- **Profile Links**: Finds `/username` patterns in links
- **@Mentions**: Extracts `@username` from text content
- **Tweet Authors**: Identifies usernames from tweet cards
- **User Cells**: Parses Twitter's UserCell components

It automatically filters out system paths like:
- `/home`, `/explore`, `/settings`
- `/i/flow`, `/tos`, `/privacy`

### 3. Deduplication

- Loads existing accounts from `accounts.csv`
- Combines with newly found accounts
- Removes duplicates automatically
- Maintains alphabetical order

## Ongoing Workflow

The scraper is designed for ongoing use:

### Week 1
```bash
# Save HTML from x.com/home → x_home/week1.html
python account_scraper.py
# Result: 50 accounts
```

### Week 2
```bash
# Save HTML again → x_home/week2.html
python account_scraper.py
# Result: 50 old + 30 new = 80 total accounts
```

### Week 3
```bash
# Save HTML again → x_home/week3.html
python account_scraper.py
# Result: 80 old + 25 new = 105 total accounts
```

Each time you run it:
- ✅ Processes **all** HTML files in `x_home/`
- ✅ Combines with existing `accounts.csv`
- ✅ Adds only new unique accounts
- ✅ No duplicates

## Tips

### Getting More Profiles

- **Scroll more** before saving (each scroll loads 10-20 new profiles)
- **Visit different feeds**: For You, Following, etc.
- **Save multiple times** over days/weeks as your feed changes
- **Save from multiple devices** (work laptop, home PC, phone via Desktop Mode)

### Managing Files

Keep all HTML files in `x_home/`:
```
x_home/
├── monday.html
├── wednesday.html
├── friday.html
├── weekend.html
```

The script processes all of them each time and combines the results.

### Cleaning Up Old Files

You can delete old HTML files if `x_home/` gets too large:
```bash
# The accounts are already saved in accounts.csv
rm x_home/old_file.html
```

The CSV persists all previously found accounts, so deleting HTML files won't affect your account list.

## Advantages Over Extension/Automation

| Feature | account_scraper.py | Chrome Extension | Playwright Scraper |
|---------|-------------------|------------------|-------------------|
| **Detection** | ✅ None | ❌ Detected by X | ⚠️ May be detected |
| **Login Required** | ❌ No | ❌ No | ✅ Yes |
| **Setup** | None | Load extension | Install browser |
| **Speed** | Instant | Fast | Slow (scrolling) |
| **Reliability** | ✅ Always works | ❌ Gets blocked | ⚠️ Sometimes fails |
| **Offline** | ✅ Yes | ❌ No | ❌ No |

## Output Format

### accounts.csv

```csv
# Accounts extracted from X/Twitter HTML pages
# Updated automatically by account_scraper.py
# One username per line
username
account1
account2
account3
...
```

The CSV format is used for:
- Easy deduplication
- Excel/Google Sheets compatibility
- Simple parsing by other scripts

## Troubleshooting

### "x_home folder not found"

**Solution**: Create the folder:
```bash
mkdir x_home
```

Then save HTML files there and run the script again.

### "No HTML files found"

**Solution**: Make sure you saved the page to the `x_home/` folder:
1. Go to x.com/home
2. Press Ctrl+S
3. Choose the `x_home/` folder as the save location
4. Save as "Webpage, Complete" or "Webpage, HTML Only"

### "Only found a few usernames"

**Cause**: You didn't scroll enough before saving.

**Solution**:
1. Go to x.com/home
2. Scroll down 10-15 times to load more content
3. Wait for content to load after each scroll
4. Save the page
5. Run the script again

### "Some usernames look wrong"

**Cause**: X/Twitter sometimes uses short account names for internal features.

**Solution**: These are automatically filtered out. If you see any that shouldn't be there, you can:
1. Edit `accounts.csv` manually to remove them
2. Or ignore them (they won't cause issues with monitoring)

### File encoding errors

**Cause**: Special characters in the HTML.

**Solution**: The script uses `encoding='utf-8', errors='ignore'` to handle this automatically. Should work with any HTML file.

## Integration with Post Monitor

Once you have `accounts.csv`, the post monitor needs to read it.

Update your `post_monitor.py` to read from CSV instead of TXT:

```python
def load_accounts_from_csv(csv_path='accounts.csv'):
    """Load accounts from CSV file"""
    accounts = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and not row[0].startswith('#'):
                username = row[0].strip()
                if username and username != 'username':
                    accounts.append(username)
    return accounts
```

Or simply convert CSV to TXT when needed:
```bash
# Extract just the usernames to accounts.txt
tail -n +5 accounts.csv | cut -d',' -f1 > accounts.txt
```

## Advanced Usage

### Process Only New Files

If you want to only process files you haven't processed yet:

1. Create a `x_home/processed/` folder
2. After running the script, move processed files there:
   ```bash
   mv x_home/*.html x_home/processed/
   ```
3. Next time, only new files in `x_home/` will be processed

### Merge Multiple Lists

If you have accounts from different sources:

```bash
# Accounts from friend's HTML
python account_scraper.py  # Processes x_home/friend.html

# Accounts from your feed
# (already in accounts.csv)

# Combined automatically!
```

### Export to Other Formats

Convert to plain text:
```bash
tail -n +5 accounts.csv | cut -d',' -f1 > accounts.txt
```

Convert to JSON:
```python
import csv
import json

accounts = []
with open('accounts.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        if row and not row[0].startswith('#') and row[0] != 'username':
            accounts.append(row[0])

with open('accounts.json', 'w') as f:
    json.dump(accounts, f, indent=2)
```

## Next Steps

After building your account list:

1. **Review accounts.csv**: Open it and verify the accounts look good
2. **Start monitoring**: Run `python post_monitor.py` (configure it to read from CSV)
3. **Add more accounts**: Save more HTML files to `x_home/` and re-run the scraper anytime
4. **Keep it updated**: Run weekly to catch new accounts from your feed

## Why This Approach Works

✅ **No Detection**: You're just reading saved files, not automating a browser
✅ **No Login**: X/Twitter's home page is public (when you're logged in to save it)
✅ **No Rate Limits**: Parsing happens offline
✅ **Reliable**: Always works, no API changes affect it
✅ **Simple**: Just save HTML and run a Python script
✅ **Ongoing**: Build your list over time naturally

The only "manual" step is saving the HTML, which takes 2 seconds (Ctrl+S). Everything else is automated!
