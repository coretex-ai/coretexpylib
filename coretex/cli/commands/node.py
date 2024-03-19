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

from typing import Optional

import click

from ..modules import node as node_module
from ..modules.ui import clickPrompt, successEcho, errorEcho, previewConfig
from ..modules.update import NodeStatus, getNodeStatus, activateAutoUpdate, dumpScript, UPDATE_SCRIPT_NAME
from ..modules.utils import onBeforeCommandExecute
from ..modules.user import initializeUserSession
from ...configuration import loadConfig, saveConfig, CONFIG_DIR, isNodeConfigured
from ...utils import docker


@click.command()
@click.option("--image", type = str, help = "Docker image url")
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def start(image: Optional[str]) -> None:
    if node_module.isRunning():
        if not clickPrompt(
            "Node is already running. Do you wish to restart the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop()

    if node_module.exists():
        node_module.clean()

    config = loadConfig()

    if image is not None:
        config["image"] = image  # store forced image (flagged) so we can run autoupdate afterwards
        saveConfig(config)

    dockerImage = config["image"]

    if node_module.shouldUpdate(dockerImage):
        node_module.pull(dockerImage)

    node_module.start(dockerImage, config)

    activateAutoUpdate(CONFIG_DIR, config)


@click.command()
def stop() -> None:
    if not node_module.isRunning():
        errorEcho("Node is already offline.")
        return

    node_module.stop()


@click.command()
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def update() -> None:
    config = loadConfig()
    dockerImage = config["image"]

    nodeStatus = getNodeStatus()

    if nodeStatus == NodeStatus.inactive:
        errorEcho("Node is not running. To update Node you need to start it first.")
        return

    if nodeStatus == NodeStatus.reconnecting:
        errorEcho("Node is reconnecting. Cannot update now.")
        return

    if nodeStatus == NodeStatus.busy:
        if not clickPrompt(
            "Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop()

    if not node_module.shouldUpdate(dockerImage):
        successEcho("Node is already up to date.")
        return

    node_module.pull(dockerImage)

    if getNodeStatus() == NodeStatus.busy:
        if not clickPrompt(
            "Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    node_module.stop()

    node_module.start(dockerImage, config)


@click.command()
@click.option("--verbose", is_flag = True, help = "Configure node settings manually.")
def config(verbose: bool) -> None:
    if node_module.isRunning():
        if not clickPrompt(
            "Node is already running. Do you wish to stop the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            errorEcho("If you wish to reconfigure your node, use coretex node stop commands first.")
            return

        node_module.stop()

    config = loadConfig()

    if isNodeConfigured(config):
        if not clickPrompt(
            "Node configuration already exists. Would you like to update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    node_module.configureNode(config, verbose)
    saveConfig(config)
    previewConfig(config)

    # Updating auto-update script since node configuration is changed
    dumpScript(CONFIG_DIR / UPDATE_SCRIPT_NAME, config)

    successEcho("Node successfully configured.")


@click.group()
@onBeforeCommandExecute(docker.isDockerAvailable)
@onBeforeCommandExecute(initializeUserSession)
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
node.add_command(update, "update")
node.add_command(config, "config")
