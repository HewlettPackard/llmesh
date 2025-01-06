#!/bin/bash

# Activate virtual environment 
source .venv/bin/activate

# List of app directories
apps_directories=(
    "examples/app_games"          #5001
)

# Activate and launch apps
for dir in "${apps_directories[@]}"; do
    (
        python "$dir/main.py" &
    )
done

wait
