# X/Twitter Profile Scraper - Chrome Extension

A Chrome extension that scrapes profile usernames from your X/Twitter "For You" feed and saves them to a text file.

## Features

- 🚀 One-click scraping from x.com/home
- 📜 Auto-scrolls to load more profiles
- 💾 Downloads profiles as `accounts.txt`
- 📊 Shows real-time statistics
- 🎨 Beautiful gradient UI
- ⚡ Fast and efficient

## Installation

### Step 1: Generate Icons

1. Open `generate-icons.html` in your browser
2. Icons will be generated automatically
3. Click "Download All"
4. Move the downloaded `icon16.png`, `icon48.png`, and `icon128.png` to the `icons/` folder

### Step 2: Load Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. The extension should now appear in your toolbar!

## Usage

### Method 1: From x.com/home

1. Navigate to [https://x.com/home](https://x.com/home)
2. Let the feed load (scroll if you want more profiles)
3. Click the extension icon in your toolbar
4. Click "Scrape Profiles"
5. Wait for the scraping to complete (it will auto-scroll 5 times)
6. Click "Download accounts.txt"

### Method 2: Direct Download

The extension will:
- Scrape all visible usernames from the feed
- Automatically scroll 5 times to load more content
- Show you a preview of found profiles
- Generate `accounts.txt` ready for your monitoring system

## How It Works

The extension uses multiple methods to find profiles:

1. **Profile Links** - Finds all `/username` links
2. **User Cells** - Looks for Twitter's UserCell components
3. **Tweet Articles** - Extracts authors from tweet cards
4. **@Mentions** - Finds any @username mentions

It filters out non-profile links (like `/home`, `/settings`, etc.) and returns only valid usernames.

## Files

```
chrome-extension/
├── manifest.json          # Extension configuration
├── popup.html            # Extension popup UI
├── popup.js              # Popup logic
├── content.js            # Content script (page scraper)
├── generate-icons.html   # Icon generator
├── icons/
│   ├── icon16.png       # 16x16 icon
│   ├── icon48.png       # 48x48 icon
│   └── icon128.png      # 128x128 icon
└── README.md            # This file
```

## Compatibility

- ✅ Chrome (v88+)
- ✅ Edge (Chromium-based)
- ✅ Brave
- ✅ Opera
- ✅ Any Chromium-based browser

## Troubleshooting

**Extension doesn't appear**
- Make sure Developer Mode is enabled
- Try reloading the extension
- Check the console for errors

**"No profiles found"**
- Make sure you're on x.com/home
- Try scrolling down manually first to load content
- Check if you're logged in to X/Twitter

**Scraping seems slow**
- The extension scrolls 5 times (7.5 seconds each)
- This is intentional to avoid rate limits
- You can modify the scroll count in `content.js` (line 132)

**Download doesn't work**
- Check Chrome's download settings
- Make sure downloads aren't blocked
- Try clicking "Download accounts.txt" again

## Integration with Monitoring System

Once you've downloaded `accounts.txt`:

1. Move it to your main project directory (where `post_monitor.py` is)
2. Or copy the contents and paste into your existing `accounts.txt`
3. Run `python post_monitor.py` to start monitoring those accounts!

## Privacy & Safety

- ✅ Extension only runs on x.com and twitter.com
- ✅ No data is sent to external servers
- ✅ All scraping happens locally in your browser
- ✅ Only reads public information
- ✅ Open source - review the code yourself!

## Customization

### Adjust Scroll Count

Edit `content.js` line 132:
```javascript
scrapeWithScroll(5)  // Change 5 to your desired number
```

### Change Scroll Delay

Edit `content.js` line 94:
```javascript
setTimeout(() => {
  // Change 1500 to your desired delay in milliseconds
}, 1500);
```

## License

MIT License - Do whatever you want with it!

## Credits

Built for the Twitter/X Early Response System.
