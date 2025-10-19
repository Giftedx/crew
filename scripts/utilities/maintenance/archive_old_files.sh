#!/bin/bash
# Archive Old Files Script
# Ultimate Discord Intelligence Bot
# Created: October 17, 2025

set -e

# Configuration
DAYS_OLD=${1:-30}
ARCHIVE_DIR="archive/automated_$(date +%Y%m%d)"

echo "📦 Archiving files older than $DAYS_OLD days..."

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Function to archive old logs
archive_old_logs() {
    echo "→ Archiving old log files..."
    mkdir -p "$ARCHIVE_DIR/logs"
    find . -name "*.log" -mtime +$DAYS_OLD -not -path "./archive/*" \
        -not -path "./venv/*" -exec mv {} "$ARCHIVE_DIR/logs/" \; 2>/dev/null || true
}

# Function to archive old JSON results
archive_old_json() {
    echo "→ Archiving old JSON files..."
    mkdir -p "$ARCHIVE_DIR/json"
    find benchmarks/results -name "*.json" -mtime +$DAYS_OLD \
        -exec mv {} "$ARCHIVE_DIR/json/" \; 2>/dev/null || true
}

# Function to archive old downloads
archive_old_downloads() {
    echo "→ Checking crew_data/Downloads..."
    if [ -d "crew_data/Downloads" ]; then
        mkdir -p "$ARCHIVE_DIR/downloads"
        find crew_data/Downloads -type f -mtime +$DAYS_OLD \
            -exec mv {} "$ARCHIVE_DIR/downloads/" \; 2>/dev/null || true
    fi
}

# Main archival
archive_old_logs
archive_old_json
archive_old_downloads

# Count archived files
COUNT=$(find "$ARCHIVE_DIR" -type f 2>/dev/null | wc -l)

if [ $COUNT -gt 0 ]; then
    echo ""
    echo "✅ Archived $COUNT files to $ARCHIVE_DIR"
    echo ""
    echo "📊 Archive size:"
    du -sh "$ARCHIVE_DIR"
else
    echo ""
    echo "ℹ️  No files older than $DAYS_OLD days found"
    rmdir "$ARCHIVE_DIR" 2>/dev/null || true
fi

echo ""
echo "💡 Usage: $0 [days_old]"
echo "   Default: 30 days"
