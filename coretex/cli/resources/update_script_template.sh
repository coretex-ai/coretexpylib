#!/bin/bash

# Define Docker-related variables
DOCKER_PATH={dockerPath}
REPOSITORY={repository}
TAG={tag}
IMAGE={repository}:{tag}
SERVER_URL={serverUrl}
STORAGE_PATH={storagePath}
NODE_ACCESS_TOKEN={nodeAccessToken}
NODE_MODE={nodeMode}
MODEL_ID={modelId}
CONTAINER_NAME={containerName}
NETWORK_NAME={networkName}
RESTART_POLICY={restartPolicy}
PORTS={ports}
CAP_ADD={capAdd}
RAM_MEMORY={ramMemory}G
SWAP_MEMORY={swapMemory}G
SHARED_MEMORY={sharedMemory}G

NODE_STATUS_ENDPOINT="http://localhost:21000/status"

# Dump logs to CLI directory
OUTPUT_DIR="$HOME/.config/coretex"
mkdir -p "$OUTPUT_DIR"

# Generate the output filename based on the current Unix timestamp
OUTPUT_FILE="$OUTPUT_DIR/ctx_autoupdate.log"

# Redirect all output to the file
exec >>"$OUTPUT_FILE" 2>&1

function fetch_node_status {{
    local api_response=$(curl -s "$NODE_STATUS_ENDPOINT")
    local status=$(echo "$api_response" | sed -n 's/.*"status":\([^,}}]*\).*/\1/p')
    echo "$status"
}}

function should_update {{
    local status=$(fetch_node_status)

    if [ "$status" -eq 2 ]; then
        echo "Checking node version..."
        # Get latest image digest from docker hub
        manifest_output=$($DOCKER_PATH manifest inspect $REPOSITORY:$TAG --verbose)

        # get digest from docker hub
        digest_line=$(echo "$manifest_output" | grep -o '"digest": ".*"' | head -n 1)
        latest_digest=$(echo "$digest_line" | cut -d '"' -f 4)

        # get digest from local container
        current_digest=$($DOCKER_PATH image ls --digests | grep $REPOSITORY | grep $TAG | awk '{{print $3}}')
        current_digest=$(echo "$current_digest" | awk '{{$1=$1;print}}')

        # Compare digests
        if [[ $latest_digest != $current_digest ]]; then
            return 0 # Return True since there is new image to be pulled from docker hub
        else
            echo "Node version is up to date."
            return 1
        fi
    else
        echo "Node is not active."
        return 1
    fi
}}

function pull_image {{
    if $DOCKER_PATH image pull "$IMAGE"; then
        echo "Image pulled successfully: $IMAGE"
        return 0
    else
        echo "Failed to pull image: $IMAGE"
        return 1
    fi
}}

# Define function to stop and remove the container
function stop_node {{
    echo "Stopping and removing the container: $CONTAINER_NAME"
    $DOCKER_PATH stop "$CONTAINER_NAME" && $DOCKER_PATH rm "$CONTAINER_NAME"

    if $DOCKER_PATH network inspect $NETWORK_NAME; then
        echo "Removing the network: $NETWORK_NAME"
        $DOCKER_PATH network rm "$NETWORK_NAME"
    fi

    echo "Node successfully stopped."
}}

# Define function to start the node with the latest image
function start_node {{
    if $DOCKER_PATH network inspect $NETWORK_NAME; then
        echo "Removing the network: $NETWORK_NAME"
        $DOCKER_PATH network rm "$NETWORK_NAME"
    fi

    echo "Creating network"
    $DOCKER_PATH network create --driver bridge $NETWORK_NAME

    echo "Starting the node with the latest image"
    start_command="$DOCKER_PATH run -d --env CTX_API_URL=$SERVER_URL --env CTX_STORAGE_PATH=$STORAGE_PATH --env CTX_NODE_ACCESS_TOKEN=$NODE_ACCESS_TOKEN --env CTX_NODE_MODE=$NODE_MODE --restart $RESTART_POLICY -p $PORTS --cap-add $CAP_ADD --network $NETWORK_NAME --memory $RAM_MEMORY --memory-swap $SWAP_MEMORY --shm-size $SHARED_MEMORY --name $CONTAINER_NAME $IMAGE"

    if [ $MODEL_ID != "None" ]; then
        start_command+=" --env CTX_MODEL_ID=$MODEL_ID"
    fi

    # Call start_command wherever you want
    eval "$start_command"
}}

# Define function to update node
function update_node {{
    local status=$(fetch_node_status)

    if [ "$status" -eq 3 ]; then
        echo "Node is busy, stopping node update."
        return 1
    fi

    echo "Updating node"
    if ! should_update; then
        return 1
    fi

    if ! pull_image; then
        return 1
    fi

    if ! stop_node; then
        return 1
    fi

    start_node
}}

# Function to run node update
function run_node_update {{
    echo "Running command: update_node"
    update_node

    local exit_code=$?
    if [ "$exit_code" -eq 0 ]; then
        echo "Node update finished successfully"
    else
        echo "Node failed to update with exit code $exit_code"
    fi
}}

# Main execution
run_node_update
