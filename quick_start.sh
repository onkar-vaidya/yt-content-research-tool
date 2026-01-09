#!/bin/bash

# Quick Start Script for Unified YouTube Scraper
# This script helps you run the unified scraper quickly

echo "=============================================="
echo "  Unified YouTube Scraper - Quick Start"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import requests, pandas, yt_dlp" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Missing dependencies!"
    echo "Installing required packages..."
    python3 -m pip install requests pandas openpyxl yt-dlp
fi

echo "✅ All dependencies installed"
echo ""

# Create output folders
echo "📁 Creating output folders..."
mkdir -p Keywords Videos
echo "✅ Folders created: Keywords/, Videos/"
echo ""

# Check for input file
if [ ! -f "InputKeywords.txt" ]; then
    echo "⚠️  InputKeywords.txt not found!"
    echo "Creating empty file..."
    touch InputKeywords.txt
    echo "Please add your keywords to InputKeywords.txt before running."
    exit 0
fi

if [ ! -s "InputKeywords.txt" ]; then
    echo "⚠️  InputKeywords.txt is empty!"
    echo "Please add your keywords to this file before running."
    # We don't exit here because the script has a fallback, but user should know
fi

# Run the script
echo "🚀 Starting unified scraper..."
echo "   (Press Ctrl+C to stop)"
echo ""
sleep 2

python3 main.py

echo ""
echo "=============================================="
echo "  ✨ Scraping Complete!"
echo "=============================================="
echo ""
echo "📊 Check your results:"
echo "   - Keywords: ./Keywords/"
echo "   - Videos:   ./Videos/"
echo ""
