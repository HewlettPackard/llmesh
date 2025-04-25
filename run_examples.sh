#!/bin/bash

# List of tools directories
tools_directories=(
    "examples/tool_copywriter"      #5002
    "examples/tool_api"             #5003
    "examples/tool_analyzer"        #5004
    "examples/tool_agents"          #5005
    "examples/tool_rag"             #5006
)

# Activate virtual environment 
source .venv/bin/activate

# Download example data files
python ./3gpp.py # Download spec files for tool_rag example

# Launch tools
for dir in "${tools_directories[@]}"; do
    (
        python "$dir/main.py" &
    )
done


# List of ports
ports=(
    5002    # Basic Copywriter
    5003    # Temperature Finder    
    5004    # Temperature Analyzer
    5005    # OpenAPI Manager
    5006    # Telco Expert
)

# Function to check if a port is in use
is_port_in_use() {
    nc -z localhost "$1" > /dev/null 2>&1
}

# Wait for all ports or until a maximum of 10 seconds
max_wait_time=30
elapsed_time=0
sleep_interval=1

while [ "$elapsed_time" -lt "$max_wait_time" ]; do
    all_ports_ready=true
    for port in "${ports[@]}"; do
        if ! is_port_in_use "$port"; then
            all_ports_ready=false
            break
        fi
    done
    if [ "$all_ports_ready" = true ]; then
        echo "All ports are ready."
        break
    fi
    echo "Waiting for ports to be ready... ($elapsed_time/$max_wait_time seconds)"
    sleep "$sleep_interval"
    elapsed_time=$((elapsed_time + sleep_interval))
done


# List of app directories
apps_directories=(
    "examples/app_memory"           #5010
    "examples/app_backpanel"        #5011
    "examples/app_chatbot"          #5001
)

# Activate and launch apps
for dir in "${apps_directories[@]}"; do
    (
        python "$dir/main.py" &
    )
done

wait
