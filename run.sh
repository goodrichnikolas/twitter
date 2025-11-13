#!/bin/bash

# Launch Chrome with remote debugging in the background
echo "Launching Chrome with remote debugging on port 9222..."
"/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
    --remote-debugging-port=9222 \
    --remote-debugging-address=0.0.0.0 \
    --user-data-dir="C:\\temp\\chrome-debug-profile" &

# Store the PID
CHROME_PID=$!

# Wait for user to select their profile
echo ""
echo "Chrome is starting..."
echo "If you see a profile selection screen, please select your profile now."
echo ""
read -p "Press Enter once you've selected your profile and Chrome is fully loaded... "

# Run the Python script
echo ""
echo "Running Python automation script..."
python chrome_test.py

# Note: Chrome will stay open after the script exits
echo ""
echo "Script finished. Chrome is still running."
