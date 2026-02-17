#!/bin/bash

# Set PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"

# Project directory
cd "$HOME/Documents/GitHub/daily-market-brief" || exit 1

# Log file
CRON_LOG="cron_log.txt"

# Start logging
{
    echo "===================================="
    echo "Run started: $(date)"
    echo "===================================="
    
    # Load .env file using set -a
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
        echo "✅ Loaded .env file"
    else
        echo "❌ .env file not found"
        exit 1
    fi
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Activated virtual environment"
    else
        echo "❌ venv not found"
        exit 1
    fi
    
    # Run Python script
    echo "🚀 Running main.py..."
    python main.py
    
    # Log completion
    echo "Exit code: $?"
    echo "Run completed: $(date)"
    echo ""
    
} >> "$CRON_LOG" 2>&1
