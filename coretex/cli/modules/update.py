from enum import IntEnum
from pathlib import Path

import requests

from .cron import jobExists, scheduleJob
from ...utils import command
from ...configuration import CONFIG_DIR


UPDATE_SCRIPT_NAME = "ctx_node_update.sh"


class NodeStatus(IntEnum):

    inactive     = 1
    active       = 2
    busy         = 3
    deleted      = 4
    reconnecting = 5


def generateUpdateScript(isHTTPS: bool) -> str:
    _, coretexPath, _ = command(["which", "coretex"], ignoreStdout = True, ignoreStderr = True)

    bashScriptTemplate = '''#!/bin/bash
NODE_UPDATE_COMMAND="{coretexPath} node update"
# Dump logs to CLI directory
OUTPUT_DIR="$HOME/.config/coretex"
mkdir -p "$OUTPUT_DIR"
# Generate the output filename based on the current Unix timestamp
OUTPUT_FILE="$OUTPUT_DIR/ctx_autoupdate.log"
# Redirect all output to the file
exec >>"$OUTPUT_FILE" 2>&1

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

function run_update {{
    run_node_update
}}

# Main execution
run_update
'''

    # Replace placeholders with actual values
    return bashScriptTemplate.format(
        coretexPath = coretexPath.strip(),
    )


def dumpScript(updateScriptPath: Path, isHTTPS: bool) -> None:
    with updateScriptPath.open("w") as scriptFile:
        scriptFile.write(generateUpdateScript(isHTTPS))

    command(["chmod", "+x", str(updateScriptPath)], ignoreStdout = True)


def activateAutoUpdate(configDir: Path, isHTTPS: bool) -> None:
    updateScriptPath = CONFIG_DIR / UPDATE_SCRIPT_NAME
    dumpScript(updateScriptPath, isHTTPS)

    if not jobExists(UPDATE_SCRIPT_NAME):
        scheduleJob(configDir, UPDATE_SCRIPT_NAME)


def getNodeStatus(isHTTPS: bool) -> NodeStatus:
    protocol = "https" if isHTTPS else "http"
    response = requests.get(f"{protocol}://localhost:21000/status", timeout = 1)
    status = response.json()["status"]
    return NodeStatus(status)
