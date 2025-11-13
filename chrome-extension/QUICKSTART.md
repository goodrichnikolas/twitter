# Quick Start Guide

## 5-Minute Setup

### 1. Generate Icons (2 minutes)

```bash
# Open this file in your browser
open generate-icons.html
```

Click "Download All" and move the icons to the `icons/` folder.

### 2. Load Extension (1 minute)

1. Open Chrome
2. Go to `chrome://extensions/`
3. Toggle "Developer mode" ON (top right)
4. Click "Load unpacked"
5. Select this `chrome-extension` folder

### 3. Use It! (2 minutes)

1. Go to [https://x.com/home](https://x.com/home)
2. Click the extension icon (puzzle piece in toolbar)
3. Click "Scrape Profiles"
4. Wait ~10 seconds (it auto-scrolls)
5. Click "Download accounts.txt"

Done! 🎉

## Tips

- The extension automatically scrolls 5 times to load more content
- You can scrape as many times as you want
- Works best on the home feed
- All data stays in your browser (nothing sent to servers)

## What's Next?

Use the downloaded `accounts.txt` with your monitoring system:

```bash
# Move to project root
mv ~/Downloads/accounts.txt .

# Start monitoring
python post_monitor.py
```

You'll now be notified when those accounts post something recent!
