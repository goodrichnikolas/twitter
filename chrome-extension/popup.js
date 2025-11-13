// Popup script for X/Twitter Profile Scraper

let scrapedProfiles = [];

// DOM elements
const scrapeBtn = document.getElementById('scrapeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const status = document.getElementById('status');
const profileList = document.getElementById('profileList');
const spinner = document.getElementById('spinner');
const stats = document.getElementById('stats');
const profileCount = document.getElementById('profileCount');
const uniqueCount = document.getElementById('uniqueCount');

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
  status.textContent = message;
  status.className = 'show ' + type;
  setTimeout(() => {
    if (type !== 'success') {
      status.classList.remove('show');
    }
  }, 5000);
}

/**
 * Show loading state
 */
function setLoading(isLoading) {
  scrapeBtn.disabled = isLoading;
  if (isLoading) {
    spinner.classList.add('show');
    scrapeBtn.textContent = 'Scraping...';
  } else {
    spinner.classList.remove('show');
    scrapeBtn.textContent = 'Scrape Profiles';
  }
}

/**
 * Update profile list display
 */
function updateProfileList(profiles) {
  if (profiles.length === 0) {
    profileList.innerHTML = '<div style="text-align: center; opacity: 0.7;">No profiles found</div>';
    return;
  }

  const html = profiles
    .slice(0, 50) // Show first 50
    .map(profile => `<div class="profile-item">@${profile}</div>`)
    .join('');

  profileList.innerHTML = html;

  if (profiles.length > 50) {
    profileList.innerHTML += `<div style="text-align: center; margin-top: 10px; opacity: 0.7;">...and ${profiles.length - 50} more</div>`;
  }

  profileList.classList.add('show');
}

/**
 * Update statistics
 */
function updateStats(total, unique) {
  profileCount.textContent = total;
  uniqueCount.textContent = unique;
  stats.style.display = 'flex';
}

/**
 * Download profiles as text file
 */
function downloadProfiles(profiles) {
  const content = profiles.join('\n');
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);

  // Create download link
  const a = document.createElement('a');
  a.href = url;
  a.download = 'accounts.txt';
  a.click();

  // Cleanup
  URL.revokeObjectURL(url);

  showStatus('✓ Downloaded accounts.txt', 'success');
}

/**
 * Scrape profiles from current tab
 */
async function scrapeProfiles() {
  setLoading(true);
  showStatus('Checking current page...');

  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Check if we're on X/Twitter
    if (!tab.url.includes('x.com') && !tab.url.includes('twitter.com')) {
      showStatus('❌ Please open x.com/home first', 'error');
      setLoading(false);
      return;
    }

    // Check if we're on the home page
    if (!tab.url.includes('/home')) {
      showStatus('❌ Please navigate to x.com/home', 'error');
      setLoading(false);
      return;
    }

    showStatus('Scraping profiles from feed...');

    // Send message to content script
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'scrapeProfiles'
    });

    if (response.success) {
      scrapedProfiles = response.profiles;

      if (scrapedProfiles.length === 0) {
        showStatus('⚠️ No profiles found. Try scrolling down first.', 'error');
        setLoading(false);
        return;
      }

      showStatus(`✓ Found ${scrapedProfiles.length} profiles!`, 'success');
      updateProfileList(scrapedProfiles);
      updateStats(scrapedProfiles.length, scrapedProfiles.length);

      // Show download button
      downloadBtn.style.display = 'block';
    } else {
      showStatus(`❌ ${response.error}`, 'error');
    }
  } catch (error) {
    console.error('Scrape error:', error);
    showStatus('❌ Error: ' + error.message, 'error');
  }

  setLoading(false);
}

// Listen for progress updates from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'SCRAPE_PROGRESS') {
    showStatus(`Scrolling... (${request.scroll}/${request.maxScrolls}) - Found ${request.count} profiles`);
  }
});

// Event listeners
scrapeBtn.addEventListener('click', scrapeProfiles);

downloadBtn.addEventListener('click', () => {
  if (scrapedProfiles.length > 0) {
    downloadProfiles(scrapedProfiles);
  }
});

// Check if we're on the right page on load
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tab = tabs[0];
  if (tab && (tab.url.includes('x.com/home') || tab.url.includes('twitter.com/home'))) {
    showStatus('✓ Ready to scrape!', 'success');
  } else {
    showStatus('⚠️ Navigate to x.com/home first', 'error');
    scrapeBtn.disabled = true;
  }
});
