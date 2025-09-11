#!/bin/bash

# Ultimate Discord Intelligence Bot - System Dependencies Installer
# Installs required system dependencies for video processing

set -e

echo "🔧 Installing System Dependencies for Ultimate Discord Intelligence Bot"
echo "=================================================================="

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 Detected Linux system"

    # Check if running in WSL
    if grep -qi microsoft /proc/version; then
        echo "🪟 Running in WSL (Windows Subsystem for Linux)"
    fi

    echo "📦 Installing ffmpeg and aria2c..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y ffmpeg aria2
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y ffmpeg aria2
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y ffmpeg aria2
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S ffmpeg aria2
    else
        echo "❌ Package manager not detected. Please install ffmpeg and aria2 manually."
        exit 1
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "🍎 Detected macOS system"
    echo "📦 Installing ffmpeg and aria2..."

    if command -v brew >/dev/null 2>&1; then
        brew install ffmpeg aria2
    else
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    echo "🪟 Detected Windows system"
    echo "❌ Please install ffmpeg manually:"
    echo "   1. Download from: https://ffmpeg.org/download.html#build-windows"
    echo "   2. Extract to a folder (e.g., C:\\ffmpeg)"
    echo "   3. Add C:\\ffmpeg\\bin to your PATH environment variable"
    exit 1

else
    echo "❓ Unknown operating system: $OSTYPE"
    echo "❌ Please install ffmpeg manually for your system"
    exit 1
fi

# Verify installation
if command -v ffmpeg >/dev/null 2>&1; then
    echo "✅ ffmpeg successfully installed at: $(which ffmpeg)"
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n1)
    echo "   Version: $ffmpeg_version"
else
    echo "❌ ffmpeg installation failed"
    exit 1
fi

echo ""
echo "🎉 System dependencies installation complete!"
echo "💡 You can now run: python -m ultimate_discord_intelligence_bot.setup_cli run discord"
