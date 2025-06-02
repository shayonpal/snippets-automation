#!/bin/bash

# Alfred Snippets Automation Runner Script
# This script activates the virtual environment and sets up environment variables

# Help function
show_help() {
    cat << EOF
Alfred Snippets Automation Runner

USAGE:
    ./run.sh [OPTIONS] [COMMAND] [ARGS...]

OPTIONS:
    -h, --help    Show this help message

COMMANDS:
    (no args)     Run interactive snippet creation from clipboard
    python3 ...   Run any Python command in the virtual environment
    bash ...      Run any bash command in the virtual environment
    <content>     Create snippet with provided content (no quotes needed)

EXAMPLES:
    ./run.sh                                    # Interactive snippet creation
    ./run.sh 158, Front St E, Toronto ON M5A 0K9   # Create snippet with address
    ./run.sh git status --porcelain                 # Create snippet with git command
    ./run.sh python3 scripts/add_alfred_snippet.py --help  # Run script with options
    ./run.sh python3 scripts/batch_import.py data.json     # Run other scripts

EOF
}

# Parse arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
esac

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
    python3 scripts/add_alfred_snippet.py
elif [ "$1" = "--add" ]; then
    # If --add flag is provided, use the rest of the arguments as the snippet content
    shift  # Remove the --add flag from arguments
    # Combine all remaining arguments without requiring quotes
    content="$*"
    python3 scripts/add_alfred_snippet.py "$content"
elif [ "$1" = "python3" ] || [ "$1" = "bash" ]; then
    # If first argument is python3 or bash, execute as command with arguments
    "$@"
else
    # Otherwise, treat all arguments as content for the snippet script
    python3 scripts/add_alfred_snippet.py "$*"
fi