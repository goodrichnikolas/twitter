#!/usr/bin/env python3
"""
Post Monitor - Monitors Twitter/X accounts for recent posts
"""

import json
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from notifier import TelegramNotifier


def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        return json.load(f)


def load_accounts(filename='accounts.csv'):
    """Load accounts to monitor from CSV or text file"""
    accounts = []

    # Try CSV first (from account_scraper.py)
    if filename.endswith('.csv'):
        try:
            import csv
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and not row[0].startswith('#'):
                        username = row[0].strip()
                        # Skip header and empty lines
                        if username and username != 'username':
                            username = username.lstrip('@')
                            accounts.append(username)
            print(f"Loaded {len(accounts)} accounts to monitor from CSV")
            return accounts
        except FileNotFoundError:
            # Try .txt file as fallback
            txt_filename = filename.replace('.csv', '.txt')
            try:
                return load_accounts(txt_filename)
            except:
                print(f"ERROR: {filename} not found.")
                print("Run account_scraper.py to generate accounts.csv")
                return []
    else:
        # Load from text file
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Remove @ if present
                        username = line.lstrip('@')
                        accounts.append(username)
            print(f"Loaded {len(accounts)} accounts to monitor from TXT")
            return accounts
        except FileNotFoundError:
            print(f"ERROR: {filename} not found.")
            print("Create accounts.txt with one username per line.")
            return []


def parse_twitter_timestamp(timestamp_text):
    """
    Parse Twitter's relative timestamp (e.g., "5m", "2h", "1d") to minutes.

    Args:
        timestamp_text: String like "5m", "2h", "1d", etc.

    Returns:
        Number of minutes ago, or None if can't parse
    """
    if not timestamp_text:
        return None

    # Clean up the text
    timestamp_text = timestamp_text.strip().lower()

    # Try to match patterns like "5m", "2h", "1d"
    match = re.match(r'(\d+)([smhd])', timestamp_text)

    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    # Convert to minutes
    if unit == 's':
        return value / 60  # seconds to minutes
    elif unit == 'm':
        return value
    elif unit == 'h':
        return value * 60
    elif unit == 'd':
        return value * 24 * 60

    return None


def check_account_recent_post(page, username, recent_minutes=10):
    """
    Check if an account has a post within the recent_minutes timeframe.

    Args:
        page: Playwright page object
        username: Twitter username
        recent_minutes: Only notify if post is within this many minutes

    Returns:
        dict with post info if recent, None otherwise
    """
    try:
        profile_url = f"https://x.com/{username}"
        print(f"  Navigating to @{username}...")
        page.goto(profile_url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)  # Let content load

        # Check if account exists
        content = page.content().lower()
        if "doesn't exist" in content or "suspended" in content:
            print(f"  Account @{username} not accessible")
            return None

        # Find the first article (tweet container)
        articles = page.locator('article[data-testid="tweet"]').all()

        if not articles:
            articles = page.locator('article').all()

        if not articles:
            print(f"  No posts found for @{username}")
            return None

        # Get the first article (latest post)
        article = articles[0]

        # Try to extract timestamp
        # Twitter shows relative timestamps like "5m", "2h" in a time element
        try:
            # Look for time element with relative timestamp
            time_elements = article.locator('time').all()

            if not time_elements:
                print(f"  No timestamp found for @{username}")
                return None

            # Get the first time element (should be the post timestamp)
            time_element = time_elements[0]

            # Try to get the relative time text (like "5m")
            # Sometimes it's in the datetime attribute, sometimes in text
            timestamp_text = None
            try:
                # Try getting the visible text first
                timestamp_text = time_element.inner_text()
            except:
                pass

            if not timestamp_text:
                print(f"  Could not extract timestamp for @{username}")
                return None

            # Parse the timestamp
            minutes_ago = parse_twitter_timestamp(timestamp_text)

            if minutes_ago is None:
                print(f"  Could not parse timestamp '{timestamp_text}' for @{username}")
                return None

            print(f"  Latest post from @{username} was {timestamp_text} ago ({minutes_ago:.1f} minutes)")

            # Check if it's recent enough
            if minutes_ago <= recent_minutes:
                # Get post URL
                try:
                    time_link = article.locator('a[href*="/status/"]').first
                    post_url = time_link.get_attribute('href')
                    if not post_url.startswith('http'):
                        post_url = f"https://x.com{post_url}"
                except:
                    post_url = profile_url

                # Try to get post text
                post_text = ""
                try:
                    text_div = article.locator('[data-testid="tweetText"]').first
                    post_text = text_div.inner_text()
                except:
                    pass

                return {
                    'username': username,
                    'url': post_url,
                    'text': post_text,
                    'timestamp': timestamp_text,
                    'minutes_ago': minutes_ago
                }
            else:
                print(f"  Post is older than {recent_minutes} minutes, skipping")
                return None

        except Exception as e:
            print(f"  Error extracting timestamp for @{username}: {e}")
            return None

    except Exception as e:
        print(f"  Error checking @{username}: {e}")
        return None


def monitor_accounts(page, accounts, notifier, recent_minutes=10):
    """
    Check accounts for recent posts.

    Args:
        page: Playwright page object
        accounts: List of usernames to monitor
        notifier: TelegramNotifier instance
        recent_minutes: Only notify if post is within this many minutes
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking {len(accounts)} accounts...")
    print(f"Will notify for posts under {recent_minutes} minutes old\n")

    recent_posts_found = 0

    for i, username in enumerate(accounts, 1):
        print(f"[{i}/{len(accounts)}] @{username}")

        recent_post = check_account_recent_post(page, username, recent_minutes)

        if recent_post:
            print(f"  🚨 RECENT POST! {recent_post['timestamp']} old")
            recent_posts_found += 1

            # Send notification
            notifier.send_new_post_notification_sync(
                username=username,
                post_url=recent_post['url'],
                post_text=recent_post['text']
            )

        # Small delay between accounts to be polite
        time.sleep(2)

    if recent_posts_found > 0:
        print(f"\n✓ Found {recent_posts_found} recent post(s)!")
    else:
        print("\n✓ No recent posts")


def main():
    """Main monitoring loop"""
    print("=" * 60)
    print("Twitter/X Recent Post Monitor")
    print("=" * 60)

    # Load configuration
    try:
        config = load_config()
        check_interval = config['monitoring']['check_interval_seconds']
        recent_minutes = config['monitoring']['recent_post_minutes']
        headless = config['monitoring'].get('headless', True)
        bot_token = config['telegram']['bot_token']
        chat_id = config['telegram']['chat_id']
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # Load accounts
    accounts = load_accounts()
    if not accounts:
        print("ERROR: No accounts to monitor")
        print("Add usernames to accounts.txt (one per line)")
        return

    # Initialize notifier
    notifier = TelegramNotifier(bot_token, chat_id)

    print(f"Monitoring {len(accounts)} accounts")
    print(f"Check interval: {check_interval} seconds ({check_interval//60} minutes)")
    print(f"Recent post threshold: {recent_minutes} minutes")
    print(f"Headless mode: {headless}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    with sync_playwright() as playwright:
        try:
            # Launch browser with persistent context to save login
            print("\nLaunching browser...")

            # Use persistent context to maintain login session
            context = playwright.chromium.launch_persistent_context(
                user_data_dir='./browser_data',  # Saves cookies/session here
                headless=headless,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.pages[0] if context.pages else context.new_page()
            print("✓ Browser launched")

            # Check if we need to log in
            # First time: go to X and let user log in
            page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)

            if "login" in page.url.lower():
                print("\n" + "=" * 60)
                print("⚠️  LOGIN REQUIRED (First Time Setup)")
                print("=" * 60)
                print("Please log in to X/Twitter in the browser window.")
                print("Your login will be saved for future runs.")
                print()
                input("Press Enter after you've logged in to continue...")
                print("\n✓ Login saved! Future runs will use this session.")
                print("=" * 60)
                print()
            else:
                print("✓ Using saved login session")
                print()

            # Send startup notification
            notifier.send_message_sync(
                "🤖 <b>Post Monitor Started</b>\n\n"
                f"Monitoring {len(accounts)} accounts\n"
                f"Checking every {check_interval//60} minutes\n"
                f"Notifying for posts under {recent_minutes} minutes old"
            )

            # Main monitoring loop
            while True:
                try:
                    monitor_accounts(page, accounts, notifier, recent_minutes)

                    # Wait until next check
                    print(f"\nNext check in {check_interval} seconds...")
                    time.sleep(check_interval)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    import traceback
                    traceback.print_exc()
                    print("Retrying in 30 seconds...")
                    time.sleep(30)

        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            notifier.send_message_sync("🛑 <b>Post Monitor Stopped</b>")
            print("✓ Goodbye!")

        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            try:
                context.close()
            except:
                pass


if __name__ == "__main__":
    main()
