#!/bin/bash

# Variables
DOCKER_PATH={dockerPath}
GIT_PATH={gitPath}
VENV_PATH={venvPath}
# Source the virtual environment
source "$VENV_PATH/activate"

# Set PATH to include the directory where docker is located
export PATH=$DOCKER_PATH:$GIT_PATH

# Execute the coretex command
$VENV_PATH/bin/coretex node update --auto >> /Users/bogdanbm/.config/coretex/logs/ctx_autoupdate.log 2>&1
