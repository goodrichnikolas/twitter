# Login Setup for Post Monitoring

## The Problem

X/Twitter requires login to view posts. The monitoring script needs to be logged in to check accounts.

## Solution: Persistent Browser Session

The updated `post_monitor.py` now saves your login session automatically.

### How It Works

1. **First Run**: Browser opens, you log in manually, session is saved
2. **Future Runs**: Script automatically uses your saved login session
3. **No Re-login Needed**: Stay logged in indefinitely

### Setup (One Time)

1. **First run with headless=false**:

   Edit `config.json`:
   ```json
   {
     "monitoring": {
       "headless": false
     }
   }
   ```

2. **Run the monitor**:
   ```bash
   python post_monitor.py
   ```

3. **Log in when prompted**:
   - Browser window will open
   - You'll see: "⚠️ LOGIN REQUIRED (First Time Setup)"
   - Log in to X/Twitter in the browser
   - Press Enter in the terminal after logging in
   - Your session is now saved!

4. **Enable headless mode** (optional):
   ```json
   {
     "monitoring": {
       "headless": true
     }
   }
   ```

5. **Future runs**: Just run `python post_monitor.py` - no login needed!

### Where Is Login Saved?

Your login session is saved in the `browser_data/` folder:
- Contains cookies and session data
- Automatically created on first run
- Already in `.gitignore` (won't be committed to git)
- Delete this folder to log out / reset

### Troubleshooting

**"Please log in" appears every time**

Possible causes:
- X/Twitter logged you out (security/inactivity)
- `browser_data/` folder was deleted
- Session expired

Solution:
- Run with `headless: false`
- Log in again
- Session will be saved again

**"Account suspended" or security checks**

X/Twitter may flag automated behavior. To minimize this:
- Use reasonable check intervals (2+ minutes)
- Don't run multiple instances
- Use the saved session (don't create new browsers)
- Consider using residential proxy (advanced)

**Session expires after a few days**

X/Twitter may expire sessions for security. If this happens:
- Run with `headless: false`
- Log in again
- Consider leaving browser visible occasionally to refresh session

### Security Notes

- ⚠️ The `browser_data/` folder contains your login cookies
- 🔒 Keep this folder secure (it's in .gitignore by default)
- 🚫 Don't share or commit this folder
- 🗑️ Delete `browser_data/` to completely log out

### Advanced: Multiple Accounts

If you want to monitor from different X/Twitter accounts:

```python
# Monitor with Account 1
context = playwright.chromium.launch_persistent_context(
    user_data_dir='./browser_data_account1',
    ...
)

# Monitor with Account 2
context = playwright.chromium.launch_persistent_context(
    user_data_dir='./browser_data_account2',
    ...
)
```

Each folder maintains a separate login session.

## Alternative Solutions

### Option 2: Cookie Export/Import

Instead of persistent context, manually export cookies:

1. Install a cookie exporter extension (e.g., "Get cookies.txt")
2. Log in to X/Twitter
3. Export cookies to `cookies.json`
4. Load cookies in script:

```python
with open('cookies.json', 'r') as f:
    cookies = json.load(f)
    context.add_cookies(cookies)
```

**Pros**: More control over cookies
**Cons**: Manual export needed, cookies expire

### Option 3: Connect to Existing Browser

Connect to a Chrome instance you keep running:

1. Launch Chrome with debugging:
   ```bash
   google-chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
   ```

2. In script:
   ```python
   browser = playwright.chromium.connect_over_cdp('http://localhost:9222')
   ```

**Pros**: Use your main browser, stays logged in
**Cons**: Need to keep Chrome running, more complex setup

### Option 4: Proxy with Rotating IPs

Use residential proxies to avoid detection:

```python
context = browser.new_context(
    proxy={
        "server": "http://proxy-server:port",
        "username": "user",
        "password": "pass"
    }
)
```

**Pros**: Harder to detect, can rotate IPs
**Cons**: Costs money, more complex

## Recommended Approach

✅ **Use the built-in persistent context** (default now)

This is the simplest and most reliable:
- No manual cookie management
- No external Chrome needed
- No proxy costs
- Just log in once and forget

## Example Flow

### First Time Setup

```bash
# 1. Set headless=false in config.json
vim config.json

# 2. Run monitor
python post_monitor.py

# Output:
# ============================================================
# Twitter/X Recent Post Monitor
# ============================================================
# Loaded 21 accounts to monitor from CSV
# ...
#
# ⚠️  LOGIN REQUIRED (First Time Setup)
# ============================================================
# Please log in to X/Twitter in the browser window.
# Your login will be saved for future runs.
#
# Press Enter after you've logged in to continue...

# 3. Log in to X in the browser window

# 4. Press Enter

# Output:
# ✓ Login saved! Future runs will use this session.
# ============================================================
#
# ✓ Using saved login session
# ...
```

### Future Runs

```bash
# Just run it - login is automatic!
python post_monitor.py

# Output:
# ============================================================
# Twitter/X Recent Post Monitor
# ============================================================
# Loaded 21 accounts to monitor from CSV
# ...
# ✓ Using saved login session
#
# Checking 21 accounts...
# ...
```

No login prompt, no browser window (if headless=true), just works!

## Summary

| Approach | Setup Difficulty | Maintenance | Reliability |
|----------|-----------------|-------------|-------------|
| **Persistent Context** | ⭐ Easy | ⭐ None | ⭐⭐⭐ High |
| Cookie Export/Import | ⭐⭐ Medium | ⭐⭐ Manual re-export | ⭐⭐ Medium |
| Existing Browser | ⭐⭐⭐ Hard | ⭐⭐ Keep running | ⭐⭐ Medium |
| Proxy + Rotation | ⭐⭐⭐⭐ Very Hard | ⭐⭐⭐ Complex | ⭐⭐⭐⭐ Very High |

**For most users**: Just use the persistent context (default). Log in once, works forever!
