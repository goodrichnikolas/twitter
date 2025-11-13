#!/usr/bin/env python3
"""
Account Scraper - Extracts usernames from manually saved X/Twitter HTML files
Scans the x_home folder for saved pages and maintains accounts.csv
"""

import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup


def extract_usernames_from_html(html_content: str) -> set[str]:
    """
    Extract usernames from X/Twitter HTML.

    Args:
        html_content: Raw HTML content from saved X/Twitter page

    Returns:
        Set of unique usernames found
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    profiles = set()

    # List of paths to skip (system pages, not user profiles)
    skip_paths = {
        'home', 'explore', 'notifications', 'messages',
        'i', 'search', 'compose', 'settings', 'tos',
        'privacy', 'about', 'status', 'intent', 'lists',
        'communities', 'hashtag'
    }

    # Method 1: Find all links with /username pattern
    links = soup.find_all('a', href=re.compile(r'^/[a-zA-Z0-9_]+$'))

    for link in links:
        href = link.get('href', '')
        if not href:
            continue

        username = href[1:]  # Remove leading /

        if username.lower() not in skip_paths:
            profiles.add(username)

    # Method 2: Look for any links that match /username pattern
    all_links = soup.find_all('a', href=True)

    for link in all_links:
        href = link['href']
        match = re.match(r'^/([a-zA-Z0-9_]+)$', href)
        if match:
            username = match.group(1)
            if username.lower() not in skip_paths:
                profiles.add(username)

    # Method 3: Look for @mentions in text
    all_text = soup.get_text()
    mention_pattern = r'@([a-zA-Z0-9_]+)'
    mentions = re.findall(mention_pattern, all_text)

    for username in mentions:
        if username.lower() not in skip_paths:
            profiles.add(username)

    # Method 4: Look for span elements with @ mentions
    spans = soup.find_all('span')

    for span in spans:
        text = span.get_text()
        if text and text.startswith('@'):
            username = text[1:].split()[0]
            if username and re.match(r'^[a-zA-Z0-9_]+$', username):
                if username.lower() not in skip_paths:
                    profiles.add(username)

    return profiles


def load_existing_accounts(csv_path: Path) -> set[str]:
    """
    Load existing accounts from CSV file.

    Args:
        csv_path: Path to accounts.csv

    Returns:
        Set of existing usernames
    """
    if not csv_path.exists():
        return set()

    existing = set()
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip empty rows and comments
                if not row or not row[0] or row[0].startswith('#'):
                    continue

                username = row[0].strip()
                if username and username != 'username':  # Skip header
                    existing.add(username)
    except Exception as e:
        print(f"Warning: Could not read existing {csv_path}: {e}")
        return set()

    return existing


def save_accounts_csv(accounts: set[str], csv_path: Path):
    """
    Save accounts to CSV file.

    Args:
        accounts: Set of usernames to save
        csv_path: Path to accounts.csv
    """
    sorted_accounts = sorted(accounts)

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header comments
        writer.writerow(['# Accounts extracted from X/Twitter HTML pages'])
        writer.writerow(['# Updated automatically by account_scraper.py'])
        writer.writerow(['# One username per line'])
        writer.writerow(['username'])

        # Write usernames
        for username in sorted_accounts:
            writer.writerow([username])


def main():
    """Main function to process saved HTML files"""
    # Configuration
    html_folder = Path('x_home')
    csv_path = Path('accounts.csv')

    print("=" * 70)
    print("X/Twitter Account Scraper - HTML Parser")
    print("=" * 70)
    print()

    # Check if x_home folder exists
    if not html_folder.exists():
        print(f"❌ Error: '{html_folder}' folder not found!")
        print()
        print("Setup instructions:")
        print(f"  1. Create the folder: mkdir {html_folder}")
        print("  2. Go to https://x.com/home in your browser")
        print("  3. Scroll down to load profiles you want to monitor")
        print("  4. Press Ctrl+S (or Cmd+S on Mac) to save the page")
        print(f"  5. Save it in the {html_folder}/ folder")
        print("  6. Run this script again")
        print()
        print(f"You can save multiple HTML files in {html_folder}/ and they'll all be processed.")
        return

    # Find all HTML files in x_home folder
    html_files = list(html_folder.glob('*.html')) + list(html_folder.glob('*.htm'))

    if not html_files:
        print(f"❌ No HTML files found in {html_folder}/")
        print()
        print("To add accounts:")
        print("  1. Go to https://x.com/home")
        print("  2. Scroll down to load profiles")
        print("  3. Press Ctrl+S to save the page")
        print(f"  4. Save it in the {html_folder}/ folder")
        print("  5. Run this script again")
        print()
        print(f"Tip: You can save multiple pages over time in {html_folder}/ to build your list!")
        return

    print(f"📁 Found {len(html_files)} HTML file(s) in {html_folder}/")
    for f in html_files:
        print(f"   • {f.name}")
    print()

    # Load existing accounts from CSV
    existing_accounts = load_existing_accounts(csv_path)
    print(f"📊 Existing accounts in {csv_path}: {len(existing_accounts)}")
    print()

    # Process all HTML files
    print("🔍 Processing HTML files...")
    print()

    all_new_profiles = set()

    for html_file in html_files:
        print(f"  Parsing: {html_file.name}")

        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            profiles = extract_usernames_from_html(html_content)
            print(f"    → Found {len(profiles)} usernames")
            all_new_profiles.update(profiles)

        except Exception as e:
            print(f"    → ❌ Error: {e}")
            continue

    print()
    print("─" * 70)
    print(f"📈 Summary:")
    print(f"   Total unique usernames found in HTML files: {len(all_new_profiles)}")

    # Combine with existing accounts
    combined_accounts = existing_accounts | all_new_profiles
    new_count = len(combined_accounts) - len(existing_accounts)

    print(f"   New accounts to add: {new_count}")
    print(f"   Total accounts after update: {len(combined_accounts)}")
    print("─" * 70)
    print()

    # Save to CSV
    save_accounts_csv(combined_accounts, csv_path)
    print(f"✅ Saved to {csv_path}")

    # Show some examples of new accounts
    if new_count > 0:
        new_accounts = sorted(all_new_profiles - existing_accounts)
        print()
        print(f"📝 Sample of new accounts added:")
        for account in new_accounts[:15]:
            print(f"     @{account}")
        if len(new_accounts) > 15:
            print(f"     ... and {len(new_accounts) - 15} more")

    print()
    print("=" * 70)
    print("✨ Done! Run this script anytime to update with new HTML files.")
    print()
    print("Next steps:")
    print("  • To add more accounts: Save more HTML files to x_home/ and re-run")
    print("  • To start monitoring: python post_monitor.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
