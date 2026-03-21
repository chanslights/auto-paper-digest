#!/bin/bash
# Cookies Backup/Restore Script
# Location: /root/.config/auto-paper-digest/cookies/

COOKIE_DIR="/root/.config/auto-paper-digest/cookies"
PROJECT_DIR="/root/auto-paper-digest/data/profiles"

backup() {
    mkdir -p "$COOKIE_DIR"
    
    echo "Backing up cookies..."
    
    # Backup cookies
    cp "$PROJECT_DIR/chrome/Cookies.json" "$COOKIE_DIR/" 2>/dev/null
    cp "$PROJECT_DIR/nblm_auth_storage.json" "$COOKIE_DIR/" 2>/dev/null
    
    # Backup Playwright profiles (if they exist)
    if [ -d "$PROJECT_DIR/default" ]; then
        rm -rf "$COOKIE_DIR/default"
        cp -r "$PROJECT_DIR/default" "$COOKIE_DIR/"
    fi
    
    if [ -d "$PROJECT_DIR/nblm_auth" ]; then
        rm -rf "$COOKIE_DIR/nblm_auth"
        cp -r "$PROJECT_DIR/nblm_auth" "$COOKIE_DIR/"
    fi
    
    echo "✅ Backup complete to $COOKIE_DIR"
    ls -la "$COOKIE_DIR"
}

restore() {
    if [ ! -d "$COOKIE_DIR" ]; then
        echo "❌ No backup found at $COOKIE_DIR"
        exit 1
    fi
    
    echo "Restoring cookies..."
    mkdir -p "$PROJECT_DIR"
    
    cp "$COOKIE_DIR/Cookies.json" "$PROJECT_DIR/chrome/" 2>/dev/null
    cp "$COOKIE_DIR/nblm_auth_storage.json" "$PROJECT_DIR/" 2>/dev/null
    
    if [ -d "$COOKIE_DIR/default" ]; then
        rm -rf "$PROJECT_DIR/default"
        cp -r "$COOKIE_DIR/default" "$PROJECT_DIR/"
    fi
    
    if [ -d "$COOKIE_DIR/nblm_auth" ]; then
        rm -rf "$PROJECT_DIR/nblm_auth"
        cp -r "$COOKIE_DIR/nblm_auth" "$PROJECT_DIR/"
    fi
    
    echo "✅ Restore complete"
}

case "$1" in
    backup)
        backup
        ;;
    restore)
        restore
        ;;
    *)
        echo "Usage: $0 {backup|restore}"
        exit 1
        ;;
esac
