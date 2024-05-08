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

from typing import Dict, Any, List, Tuple
from enum import IntEnum
from pathlib import Path

import requests

from . import config_defaults
from .cron import jobExists, scheduleJob
from .node import getRepoFromImageUrl, getTagFromImageUrl
from ..resources import RESOURCES_DIR, START_SCRIPT_NAME, UPDATE_SCRIPT_NAME
from ...utils import command
from ...configuration import CONFIG_DIR, getInitScript


class NodeStatus(IntEnum):

    inactive     = 1
    active       = 2
    busy         = 3
    deleted      = 4
    reconnecting = 5


def generateUpdateScript(config: Dict[str, Any]) -> str:
    _, dockerPath, _ = command(["which", "docker"], ignoreStdout = True, ignoreStderr = True)
    bashScriptTemplatePath = RESOURCES_DIR / "update_script_template.sh"

    with bashScriptTemplatePath.open("r") as scriptFile:
        bashScriptTemplate = scriptFile.read()

    return bashScriptTemplate.format(
        dockerPath = dockerPath.strip(),
        repository = getRepoFromImageUrl(config["image"]),
        tag = getTagFromImageUrl(config["image"]),
        containerName = config_defaults.DOCKER_CONTAINER_NAME,
        networkName = config_defaults.DOCKER_CONTAINER_NETWORK
    )


def generateStartScript(config: Dict[str, Any]) ->  str:
    _, dockerPath, _ = command(["which", "docker"], ignoreStdout = True, ignoreStderr = True)
    bashScriptTemplatePath = RESOURCES_DIR / "start_script_template.sh"

    with bashScriptTemplatePath.open("r") as scriptFile:
        bashScriptTemplate = scriptFile.read()

    return bashScriptTemplate.format(
        dockerPath = dockerPath.strip(),
        serverUrl = config["serverUrl"],
        containerName = config_defaults.DOCKER_CONTAINER_NAME,
        networkName = config_defaults.DOCKER_CONTAINER_NETWORK,
        storagePath = config["storagePath"],
        repository = getRepoFromImageUrl(config["image"]),
        tag = getTagFromImageUrl(config["image"]),
        nodeAccessToken = config["nodeAccessToken"],
        nodeMode = config["nodeMode"],
        modelId = config.get("modelId"),
        restartPolicy = "always",
        ports = "21000:21000",
        capAdd = "SYS_PTRACE",
        ramMemory = config["nodeRam"],
        swapMemory = config["nodeSwap"],
        sharedMemory = config["nodeSharedMemory"],
        cpuCount = config.get("cpuCount", config_defaults.DEFAULT_CPU_COUNT),
        imageType = "cpu" if config["allowGpu"] is False else "gpu",
        allowDocker = config.get("allowDocker", False),
        initScript = getInitScript(config),
        nodeSecret = config.get("nodeSecret", config_defaults.DEFAULT_NODE_SECRET)
    )


def dumpScripts(scripts: List[Tuple[Path, str]]) -> None:
    for script in scripts:
        path, content = script
        with path.open("w") as scriptFile:
            scriptFile.write(content)

        command(["chmod", "+x", str(path)], ignoreStdout = True)


def activateAutoUpdate(configDir: Path, config: Dict[str, Any]) -> None:
    startScript = (CONFIG_DIR / START_SCRIPT_NAME, generateStartScript(config))
    updateScript = (CONFIG_DIR / UPDATE_SCRIPT_NAME, generateUpdateScript(config))
    dumpScripts([startScript, updateScript])

    if not jobExists(UPDATE_SCRIPT_NAME):
        scheduleJob(configDir, UPDATE_SCRIPT_NAME)


def getNodeStatus() -> NodeStatus:
    try:
        response = requests.get(f"http://localhost:21000/status", timeout = 1)
        status = response.json()["status"]
        return NodeStatus(status)
    except:
        return NodeStatus.inactive