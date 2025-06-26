#!/bin/bash

# List of ports
ports=(
    5001    # Orchestrator
    5002    # Chat Service
    5003    # RAG Service
    5004    # Agents Service
    5011    # Backpanel
)


# Loop through each port
for port in "${ports[@]}"; do
    # Find the PID of the process using the port
    pids=$(lsof -t -i :$port)

    # Check if any PID is found
    if [ -z "$pids" ]; then
        echo "No process found using port $port"
    else
        # Loop through each PID and kill it
        for pid in $pids; do
            echo "Killing process $pid using port $port"
            kill $pid

            # Verify if the process has been killed
            if kill -0 $pid > /dev/null 2>&1; then
                echo "Process $pid is still running. Forcing termination..."
                kill -9 $pid
                if [ $? -eq 0 ]; then
                    echo "Process $pid has been forcefully terminated."
                else
                    echo "Failed to terminate process $pid."
                fi
            else
                echo "Process $pid has been terminated."
            fi
        done
    fi
done
