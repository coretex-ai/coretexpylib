#!/bin/bash

# Define Docker-related variables
DOCKER_PATH={dockerPath}
REPOSITORY={repository}
TAG={tag}
IMAGE={repository}:{tag}
SERVER_URL={serverUrl}
STORAGE_PATH={storagePath}
NODE_ACCESS_TOKEN={nodeAccessToken}
CONTAINER_NAME={containerName}
NETWORK_NAME={networkName}


# Define function to stop and remove the container
function stop_and_remove_container {{
    echo "Stopping and removing the container: $CONTAINER_NAME"
    $DOCKER_PATH stop "$CONTAINER_NAME" && $DOCKER_PATH rm "$CONTAINER_NAME"
}}

# Define function to remove the network
function remove_network {{
    echo "Removing the network: $NETWORK_NAME"
    $DOCKER_PATH network rm "$NETWORK_NAME"
}}

function check_version {{
    echo "Checking node version..."

    # Get latest image digest from docker hub
    manifest_output=$($DOCKER_PATH manifest inspect coretexai/coretex-node:latest-cpu --verbose)

    # get digest from docker hub
    digest_line=$(echo "$manifest_output" | grep -o '"digest": ".*"' | head -n 1)
    latest_digest=$(echo "$digest_line" | cut -d '"' -f 4)

    # get digest from local container 
    current_digest=$($DOCKER_PATH image ls --digests | grep "coretexai/coretex-node" | grep "latest-cpu" | awk '{{print $3}}')
    current_digest=$(echo "$current_digest" | awk '{{$1=$1;print}}')

    # Compare digests
    if [[ $latest_digest != $current_digest ]]; then
        return 1 # Return False since there is new image to be pulled from docker hub
    else
        echo "Node version is up to date."
        exit 0
    fi
}}

# Define function to pull the latest image
function pull_latest_image {{
    echo "Pulling the latest image from Docker Hub: $IMAGE"
    $DOCKER_PATH image pull "$IMAGE"
}}

function network_exists {{
    if $DOCKER_PATH network inspect $NETWORK_NAME >/dev/null 2>&1; then
        return 0  # Return success code
    else
        return 1  # Return error code
    fi
}}

# Define function to create the network
function create_network {{
    if network_exists; then
        remove_network
    fi

    echo "Creating network"
    $DOCKER_PATH network create --driver bridge $NETWORK_NAME
}}

# Define function to start the node with the latest image
function start_node {{
    echo "Starting the node with the latest image"
    $DOCKER_PATH run -d --env "serverUrl=$SERVER_URL" --env "storagePath=$STORAGE_PATH" --env "nodeAccessToken=$NODE_ACCESS_TOKEN" --restart "always" -p "21000:21000" --cap-add "SYS_PTRACE" --network "$NETWORK_NAME" --memory "16G" --memory-swap "32G" --shm-size "8G" --name "$CONTAINER_NAME" "$IMAGE"
}}

# Define function to update node
function update_node {{
    echo "Updating node"
    if ! check_version; then
        stop_and_remove_container
        remove_network
        pull_latest_image
        create_network
        start_node
    fi
}}

# Main execution
NODE_UPDATE_COMMAND="update_node"

# Dump logs to CLI directory
OUTPUT_DIR="$HOME/.config/coretex"
mkdir -p "$OUTPUT_DIR"

# Generate the output filename based on the current Unix timestamp
OUTPUT_FILE="$OUTPUT_DIR/ctx_autoupdate.log"

# Redirect all output to the file
exec >>"$OUTPUT_FILE" 2>&1

# Function to run node update
function run_node_update {{
    echo "Running command: $NODE_UPDATE_COMMAND"
    $NODE_UPDATE_COMMAND

    local exit_code=$?
    if [ "$exit_code" -eq 0 ]; then
        echo "Node update finished successfully"
    else
        echo "Node failed to update with exit code $exit_code"
    fi
}}

# Function to run update
function run_update {{
    run_node_update
}}

# Main execution
run_update