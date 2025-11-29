#!/bin/bash

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if BOT_TOKEN is set
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Error: BOT_TOKEN is not set!"
    echo "Please create a .env file with your bot token:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Edit and add your token"
    exit 1
fi

echo "🤖 Starting TOJI CHK Bot..."
python3 main.py
