from enum import IntEnum

import requests

from ...utils import command
from ...configuration import CONFIG_DIR

from .cron import jobExists, scheduleJob


UPDATE_SCRIPT_NAME = "ctx_node_update.sh"
IS_SSL = False


class NodeStatus(IntEnum):

    Inactive = 1
    Active = 2
    Busy = 3
    Deleted = 4
    Reconnecting = 5


def generateUpdateScript() -> str:
    _, coretexPath, _ = command(["which", "coretex"], ignoreStderr = True)

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
    bashScript = bashScriptTemplate.format(
        coretexPath = coretexPath,
        protocol = "https" if IS_SSL else "http"
    )

    return bashScript


def dumpScript(updateScriptPath: str) -> None:
    with open(updateScriptPath, "w+") as scriptFile:
        scriptFile.write(generateUpdateScript())

    command(["chmod", "+x", updateScriptPath])


def activateAutoUpdate(configDir: str, isHTTPS: bool) -> None:
    IS_SSL = isHTTPS

    updateScriptPath = str(CONFIG_DIR / UPDATE_SCRIPT_NAME)
    dumpScript(updateScriptPath)

    if (not jobExists(UPDATE_SCRIPT_NAME)):
        scheduleJob(configDir, UPDATE_SCRIPT_NAME)


def getNodeStatus() -> NodeStatus:
    protocol = 'https' if IS_SSL else 'http'
    result = requests.get(f"{protocol}://localhost:21000/status", timeout = 1)
    return NodeStatus.Active
