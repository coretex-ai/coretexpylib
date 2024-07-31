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
from ..modules.ui import clickPrompt, stdEcho, successEcho, errorEcho, previewConfig
from ..modules.update import NodeStatus, getNodeStatus, activateAutoUpdate
from ..modules.utils import onBeforeCommandExecute, checkEnvironment
from ..modules.user import initializeUserSession
from ...configuration import loadConfig, saveConfig, isNodeConfigured
from ...utils import docker


@click.command()
@click.option("--image", type = str, help = "Docker image url")
@click.option("--verbose", "verbose", is_flag = True, help = "Shows detailed about of command execution.")
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def start(image: Optional[str], verbose: bool = False) -> None:
    if node_module.isRunning(verbose):
        if not clickPrompt(
            "Node is already running. Do you wish to restart the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop(verbose)

    if node_module.exists(verbose):
        node_module.clean(verbose)

    config = loadConfig()

    if image is not None:
        config["image"] = image  # store forced image (flagged) so we can run autoupdate afterwards
        saveConfig(config)

    dockerImage = config["image"]

    if node_module.shouldUpdate(dockerImage, verbose):
        node_module.pull(dockerImage, verbose)

    node_module.start(dockerImage, config, verbose)
    docker.removeDanglingImages(
        node_module.getRepoFromImageUrl(dockerImage),
        node_module.getTagFromImageUrl(dockerImage),
        verbose
    )

    activateAutoUpdate()


@click.command()
@click.option("--verbose", "verbose", is_flag = True, help = "Shows detailed about of command execution.")
def stop(verbose: bool = False) -> None:
    if not node_module.isRunning(verbose):
        errorEcho("Node is already offline.")
        return

    node_module.stop(verbose)


@click.command()
@click.option("-y", "autoAccept", is_flag = True, help = "Accepts all prompts.")
@click.option("-n", "autoDecline", is_flag = True, help = "Declines all prompts.")
@click.option("--verbose", "verbose", is_flag = True, help = "Shows detailed about of command execution.")
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def update(autoAccept: bool, autoDecline: bool, verbose: bool = False) -> None:
    if autoAccept and autoDecline:
        errorEcho("Only one of the flags (\"-y\" or \"-n\") can be used at the same time.")
        return

    config = loadConfig()
    dockerImage = config["image"]

    nodeStatus = getNodeStatus()

    if nodeStatus == NodeStatus.inactive:
        errorEcho("Node is not running. To update Node you need to start it first.")
        return

    if nodeStatus == NodeStatus.reconnecting:
        errorEcho("Node is reconnecting. Cannot update now.")
        return

    if nodeStatus == NodeStatus.busy and not autoAccept:
        if autoDecline:
            return

        if not clickPrompt(
            "Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop(verbose)

    if not node_module.shouldUpdate(dockerImage, verbose):
        successEcho("Node is already up to date.")
        return

    stdEcho("Updating node...")
    node_module.pull(dockerImage, verbose)

    if getNodeStatus() == NodeStatus.busy and not autoAccept:
        if autoDecline:
            return

        if not clickPrompt(
            "Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    node_module.stop(verbose)

    stdEcho("Updating node...")
    node_module.start(dockerImage, config, verbose)
    docker.removeDanglingImages(
        node_module.getRepoFromImageUrl(dockerImage),
        node_module.getTagFromImageUrl(dockerImage),
        verbose
    )

    activateAutoUpdate()


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

    successEcho("Node successfully configured.")
    activateAutoUpdate()


@click.group()
@onBeforeCommandExecute(docker.isDockerAvailable)
@onBeforeCommandExecute(initializeUserSession)
@onBeforeCommandExecute(node_module.checkResourceLimitations)
@onBeforeCommandExecute(checkEnvironment)
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
node.add_command(update, "update")
node.add_command(config, "config")
