#!/bin/bash

# Alfred Snippets Automation Runner Script
# This script activates the virtual environment and sets up environment variables

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a  # automatically export all variables
    source "$SCRIPT_DIR/.env"
    set +a  # turn off automatic export
fi

# Change to script directory to ensure correct paths
cd "$SCRIPT_DIR"

# Run the command with arguments
if [ $# -eq 0 ]; then
    # If no arguments provided, run the ad hoc script to read from clipboard
    exec python3 scripts/add_alfred_snippet.py
else
    exec "$@"
fi