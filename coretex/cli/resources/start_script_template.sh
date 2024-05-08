#!/bin/bash

#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.


DOCKER_PATH={dockerPath}
CONTAINER_NAME={containerName}
NETWORK_NAME={networkName}
REPOSITORY={repository}
TAG={tag}
IMAGE={repository}:{tag}
SERVER_URL={serverUrl}
STORAGE_PATH={storagePath}
NODE_ACCESS_TOKEN={nodeAccessToken}
NODE_MODE={nodeMode}
MODEL_ID={modelId}
RESTART_POLICY={restartPolicy}
PORTS={ports}
CAP_ADD={capAdd}
RAM_MEMORY={ramMemory}G
SWAP_MEMORY={swapMemory}G
SHARED_MEMORY={sharedMemory}G
CPU_COUNT={cpuCount}
IMAGE_TYPE={imageType}
ALLOW_DOCKER={allowDocker}
INIT_SCRIPT={initScript}
NODE_SECRET={nodeSecret}

remove_image() {{
    imageID="$1"
    docker image rm "$imageID"
}}

remove_dangling_images() {{
    # Get list of images with tags
    images=$(docker image ls "$REPOSITORY" --format "{{.Repository}}:{{.Tag}}")
    echo "$images"

    # Loop through images
    while IFS= read -r image; do
        # Extract repository and tag from the image
        repository_name=$(echo "$image" | cut -d ':' -f1)
        image_tag=$(echo "$image" | cut -d ':' -f2)
        echo "$repository_name | $image_tag"

        # Check if tag is outdated
        if [ "$image_tag" != "$TAG" ]; then
            # Get the image ID
            image_id=$(docker image ls --format "{{.ID}}" "$repository_name:$image_tag")
            remove_image "$image_id"
        fi
    done <<< "$images"
}}

start_node() {{
    if $DOCKER_PATH network inspect $NETWORK_NAME; then
        echo "Removing the network: $NETWORK_NAME"
        $DOCKER_PATH network rm "$NETWORK_NAME"
    fi

    echo "Creating network"
    $DOCKER_PATH network create --driver bridge $NETWORK_NAME

    echo "Starting the node with the latest image"
    start_command="$DOCKER_PATH run -d --env CTX_API_URL=$SERVER_URL --env CTX_STORAGE_PATH=/root/.coretex --env CTX_NODE_ACCESS_TOKEN=$NODE_ACCESS_TOKEN --env CTX_NODE_MODE=$NODE_MODE --restart $RESTART_POLICY -p $PORTS --cap-add $CAP_ADD --network $NETWORK_NAME --memory $RAM_MEMORY --memory-swap $SWAP_MEMORY --shm-size $SHARED_MEMORY --cpus $CPU_COUNT --name $CONTAINER_NAME -v $STORAGE_PATH:/root/.coretex"

    if [ $IMAGE_TYPE = "gpu" ]; then
        # Run Docker command with GPU support
        start_command+=" --gpus all"
    fi

    if [ $MODEL_ID != "None" ]; then
        start_command+=" --env CTX_MODEL_ID=$MODEL_ID"
    fi

    if [ $NODE_SECRET != "" ]; then
        start_command+=" --env CTX_NODE_SECRET=$NODE_SECRET"
    fi

    if [ $ALLOW_DOCKER == "True" ]; then
        start_command+=" -v /var/run/docker.sock:/var/run/docker.sock"
    fi

    if [ $INIT_SCRIPT != "None" ]; then
        start_command+=" -v $INIT_SCRIPT:/script/init.sh"
    fi

    # Docker image must always be the last parameter of docker run command
    start_command+=" $IMAGE"
    eval "$start_command"
}}

# function to run node update
run_node_start() {{
    echo "Running command: \"coretex node start\"."
    start_node
    remove_dangling_images

    exit_code=$?
    if [ "$exit_code" -eq 0 ]; then
        echo "Node started successfully."
    else
        echo "\"coretex node start\" command failed with exit code $exit_code"
    fi
}}

# Main execution
run_node_start
