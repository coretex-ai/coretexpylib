#!/bin/bash

# Variables
DOCKER_PATH={dockerPath}
GIT_PATH={gitPath}
VENV_PATH={venvPath}

# Set PATH to include the directory where docker is located
export PATH=$DOCKER_PATH:$GIT_PATH

# Execute the "coretex node update" command
. "$VENV_PATH/bin/activate" && which coretex && coretex node update -n
