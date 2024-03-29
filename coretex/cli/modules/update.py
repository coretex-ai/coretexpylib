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

from enum import IntEnum
from pathlib import Path

import requests

from . import config_defaults
from .cron import jobExists, scheduleJob
from .node import getRepoFromImageUrl, getTagFromImageUrl
from ..resources import RESOURCES_DIR
from ...utils import command
from ...configuration import CONFIG_DIR, UserConfiguration, NodeConfiguration


UPDATE_SCRIPT_NAME = "ctx_node_update.sh"


class NodeStatus(IntEnum):

    inactive     = 1
    active       = 2
    busy         = 3
    deleted      = 4
    reconnecting = 5


def generateUpdateScript(userConfig: UserConfiguration, nodeConfig: NodeConfiguration) -> str:
    _, dockerPath, _ = command(["which", "docker"], ignoreStdout = True, ignoreStderr = True)
    bashScriptTemplatePath = RESOURCES_DIR / "update_script_template.sh"

    with bashScriptTemplatePath.open("r") as scriptFile:
        bashScriptTemplate = scriptFile.read()

    return bashScriptTemplate.format(
        dockerPath = dockerPath.strip(),
        repository = getRepoFromImageUrl(nodeConfig.image),
        tag = getTagFromImageUrl(nodeConfig.image),
        serverUrl = userConfig.serverUrl,
        storagePath = nodeConfig.storagePath,
        nodeAccessToken = nodeConfig.nodeAccessToken,
        nodeMode = nodeConfig.nodeMode,
        modelId = nodeConfig.modelId,
        containerName = config_defaults.DOCKER_CONTAINER_NAME,
        networkName = config_defaults.DOCKER_CONTAINER_NETWORK,
        restartPolicy = "always",
        ports = "21000:21000",
        capAdd = "SYS_PTRACE",
        ramMemory = nodeConfig.nodeRam,
        swapMemory = nodeConfig.nodeSwap,
        sharedMemory = nodeConfig.nodeSharedMemory,
        cpuCount = nodeConfig.cpuCount,
        imageType = "cpu" if nodeConfig.allowGpu is False else "gpu",
        allowDocker = nodeConfig.allowDocker,
        initScript = nodeConfig.getInitScriptPath()
    )


def dumpScript(updateScriptPath: Path, userConfig: UserConfiguration, nodeConfig: NodeConfiguration) -> None:
    with updateScriptPath.open("w") as scriptFile:
        scriptFile.write(generateUpdateScript(userConfig, nodeConfig))

    command(["chmod", "+x", str(updateScriptPath)], ignoreStdout = True)


def activateAutoUpdate(configDir: Path, userConfig: UserConfiguration, nodeConfig: NodeConfiguration) -> None:
    updateScriptPath = CONFIG_DIR / UPDATE_SCRIPT_NAME
    dumpScript(updateScriptPath, userConfig, nodeConfig)

    if not jobExists(UPDATE_SCRIPT_NAME):
        scheduleJob(configDir, UPDATE_SCRIPT_NAME)


def getNodeStatus() -> NodeStatus:
    try:
        response = requests.get(f"http://localhost:21000/status", timeout = 1)
        status = response.json()["status"]
        return NodeStatus(status)
    except:
        return NodeStatus.inactive
