#!/bin/bash

echo "Starting example games..."
PROJECT_ROOT=$(dirname "$(dirname "$(realpath "$0")")")

cd "$PROJECT_ROOT"

echo "Project root is: $PROJECT_ROOT"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please create it first within $PROJECT_ROOT directory."
    exit 1
fi
source .venv/bin/activate

# List of app directories
apps_directories=(
    "src/platform/app_games"          #5001
)

# Activate and launch apps
for dir in "${apps_directories[@]}"; do
    (
        python "$dir/main.py" &
    )
done

wait
