#!/bin/bash
set -e

echo "=== Installing Auto Paper Digest Dependencies ==="

# Install system dependencies
echo "Installing system packages..."
apt-get update
apt-get install -y \
    mesa-libgbm \
    alsa-lib \
    libnss3 \
    libxkbcommon0 \
    libgbm1 \
    x11-utils \
    xauth \
    xvfb \
    tigervnc \
    wget

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install \
    playwright \
    beautifulsoup4 \
    lxml \
    requests \
    click \
    python-dotenv

# Install Playwright browsers
echo "Installing Playwright Chromium..."
playwright install chromium
playwright install-deps chromium

# Clone repo if needed (for fresh environments)
if [ ! -d "/root/auto-paper-digest" ]; then
    echo "Cloning repo..."
    cd /root
    git clone https://github.com/chanslights/auto-paper-digest.git
    cd auto-paper-digest
    pip install -e .
fi

# Restore cookies if backup exists
if [ -d "/root/.config/auto-paper-digest/cookies" ]; then
    echo "Restoring cookies from backup..."
    mkdir -p /root/auto-paper-digest/data/profiles/
    cp -r /root/.config/auto-paper-digest/cookies/* /root/auto-paper-digest/data/profiles/
fi

echo "=== Setup Complete ==="
echo ""
echo "To start VNC server:"
echo "  vncserver :1 -geometry 1280x720 -depth 24"
echo ""
echo "To run the pipeline:"
echo "  DISPLAY=:1 python3 -m apd.cli run -w 2026-12"
