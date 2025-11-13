// Content script to scrape profiles from X/Twitter For You feed

/**
 * Scrape profiles from the current page
 */
function scrapeProfiles() {
  const profiles = new Set();

  // Method 1: Find all links with usernames
  // Twitter/X uses links like /username or @username
  const links = document.querySelectorAll('a[href^="/"]');

  links.forEach(link => {
    const href = link.getAttribute('href');

    if (!href) return;

    // Extract username from various patterns
    // Pattern: /username (profile links)
    const usernameMatch = href.match(/^\/([a-zA-Z0-9_]+)$/);

    if (usernameMatch) {
      const username = usernameMatch[1];

      // Filter out non-profile links
      const skipPaths = [
        'home', 'explore', 'notifications', 'messages',
        'i', 'search', 'compose', 'settings', 'tos',
        'privacy', 'about', 'status', 'intent'
      ];

      if (!skipPaths.includes(username.toLowerCase())) {
        profiles.add(username);
      }
    }
  });

  // Method 2: Look for profile cards with data-testid
  const userCells = document.querySelectorAll('[data-testid="UserCell"]');

  userCells.forEach(cell => {
    // Try to find the username link within the cell
    const userLink = cell.querySelector('a[href^="/"]');
    if (userLink) {
      const href = userLink.getAttribute('href');
      const usernameMatch = href.match(/^\/([a-zA-Z0-9_]+)$/);
      if (usernameMatch) {
        profiles.add(usernameMatch[1]);
      }
    }
  });

  // Method 3: Look for article elements (tweets) and extract authors
  const articles = document.querySelectorAll('article[data-testid="tweet"]');

  articles.forEach(article => {
    // Find the author link (usually the first link in the article)
    const authorLinks = article.querySelectorAll('a[href^="/"]');

    for (const link of authorLinks) {
      const href = link.getAttribute('href');
      const usernameMatch = href.match(/^\/([a-zA-Z0-9_]+)$/);

      if (usernameMatch) {
        profiles.add(usernameMatch[1]);
        break; // Only get the first valid username (the author)
      }
    }
  });

  // Method 4: Look for span elements with @ mentions
  const spans = document.querySelectorAll('span');

  spans.forEach(span => {
    const text = span.textContent;
    if (text && text.startsWith('@')) {
      const username = text.substring(1).split(/\s/)[0]; // Remove @ and get first word
      if (username && /^[a-zA-Z0-9_]+$/.test(username)) {
        profiles.add(username);
      }
    }
  });

  return Array.from(profiles).sort();
}

/**
 * Scroll the page to load more content
 */
function scrollPage() {
  return new Promise((resolve) => {
    const scrollHeight = document.documentElement.scrollHeight;
    window.scrollTo(0, document.body.scrollHeight);

    // Wait for content to load
    setTimeout(() => {
      const newScrollHeight = document.documentElement.scrollHeight;
      resolve(newScrollHeight > scrollHeight);
    }, 1500);
  });
}

/**
 * Scrape profiles with progressive scrolling
 */
async function scrapeWithScroll(maxScrolls = 5) {
  let allProfiles = new Set();
  let scrollCount = 0;
  let hasMore = true;

  while (scrollCount < maxScrolls && hasMore) {
    // Scrape current view
    const currentProfiles = scrapeProfiles();
    currentProfiles.forEach(profile => allProfiles.add(profile));

    // Send progress update
    chrome.runtime.sendMessage({
      type: 'SCRAPE_PROGRESS',
      count: allProfiles.size,
      scroll: scrollCount + 1,
      maxScrolls: maxScrolls
    });

    // Scroll and wait
    hasMore = await scrollPage();
    scrollCount++;
  }

  return Array.from(allProfiles).sort();
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scrapeProfiles') {
    // Check if we're on the home page
    if (!window.location.href.includes('x.com/home') &&
        !window.location.href.includes('twitter.com/home')) {
      sendResponse({
        success: false,
        error: 'Please navigate to x.com/home first'
      });
      return;
    }

    // Start scraping with scrolling
    scrapeWithScroll(5).then(profiles => {
      sendResponse({
        success: true,
        profiles: profiles,
        count: profiles.length
      });
    }).catch(error => {
      sendResponse({
        success: false,
        error: error.message
      });
    });

    // Return true to indicate async response
    return true;
  }

  if (request.action === 'scrapeQuick') {
    // Quick scrape without scrolling
    const profiles = scrapeProfiles();
    sendResponse({
      success: true,
      profiles: profiles,
      count: profiles.length
    });
  }
});

console.log('X/Twitter Profile Scraper content script loaded');
