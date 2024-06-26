#!/bin/bash

# Variables
DOCKER_PATH={dockerPath}
GIT_PATH={gitPath}
VENV_PATH={venvPath}
CONFIG_PATH={configPath}
# Source the virtual environment
source "$VENV_PATH/activate"

# Set PATH to include the directory where docker is located
export PATH=$DOCKER_PATH:$GIT_PATH

# Execute the coretex command
$VENV_PATH/bin/coretex node update -n >> $CONFIG_PATH/logs/ctx_autoupdate.log 2>&1
