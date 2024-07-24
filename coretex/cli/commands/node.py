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

from ...utils import docker
from ..modules import ui
from ..modules import node as node_module
from ..modules.node import NodeStatus
from ..modules.user import initializeUserSession
from ..modules.utils import onBeforeCommandExecute, checkEnvironment
from ..modules.update import activateAutoUpdate, getNodeStatus
from ...configuration import UserConfiguration, NodeConfiguration


@click.command()
@click.option("--image", type = str, help = "Docker image url")
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def start(image: Optional[str]) -> None:
    if node_module.isRunning():
        if not ui.clickPrompt(
            "Node is already running. Do you wish to restart the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop()

    if node_module.exists():
        node_module.clean()

    nodeConfig = NodeConfiguration()
    userConfig = UserConfiguration()

    if image is not None:
        nodeConfig.image = image  # store forced image (flagged) so we can run autoupdate afterwards
        nodeConfig.save()

    dockerImage = nodeConfig.image

    # if node_module.shouldUpdate(dockerImage):
    #     node_module.pull(dockerImage)

    node_module.start(dockerImage, userConfig, nodeConfig)
    docker.removeDanglingImages(node_module.getRepoFromImageUrl(dockerImage), node_module.getTagFromImageUrl(dockerImage))
    activateAutoUpdate()


@click.command()
def stop() -> None:
    if not node_module.isRunning():
        ui.errorEcho("Node is already offline.")
        return

    node_module.stop()


@click.command()
@click.option("-y", "autoAccept", is_flag = True, help = "Accepts all prompts.")
@click.option("-n", "autoDecline", is_flag = True, help = "Declines all prompts.")
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def update(autoAccept: bool, autoDecline: bool) -> None:
    if autoAccept and autoDecline:
        ui.errorEcho("Only one of the flags (\"-y\" or \"-n\") can be used at the same time.")
        return

    userConfig = UserConfiguration()
    nodeConfig = NodeConfiguration()

    nodeStatus = node_module.getNodeStatus()

    if nodeStatus == NodeStatus.inactive:
        ui.errorEcho("Node is not running. To update Node you need to start it first.")
        return

    if nodeStatus == NodeStatus.reconnecting:
        ui.errorEcho("Node is reconnecting. Cannot update now.")
        return

    if nodeStatus == NodeStatus.busy and not autoAccept:
        if autoDecline:
            return

        if not ui.clickPrompt(
            "Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop()

    if not node_module.shouldUpdate(nodeConfig.image):
        ui.successEcho("Node is already up to date.")
        return

    ui.stdEcho("Updating node...")
    node_module.pull(nodeConfig.image)

    if getNodeStatus() == NodeStatus.busy and not autoAccept:
        if autoDecline:
            return

        if not ui.clickPrompt(
            "Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    node_module.stop()

    ui.stdEcho("Updating node...")
    node_module.start(nodeConfig.image, userConfig, nodeConfig)

    docker.removeDanglingImages(
        node_module.getRepoFromImageUrl(nodeConfig.image),
        node_module.getTagFromImageUrl(nodeConfig.image)
    )


@click.command()
@click.option("--verbose", is_flag = True, help = "Configure node settings manually.")
def config(verbose: bool) -> None:
    if node_module.isRunning():
        if not ui.clickPrompt(
            "Node is already running. Do you wish to stop the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            ui.errorEcho("If you wish to reconfigure your node, use coretex node stop commands first.")
            return

        node_module.stop()

    userConfig = UserConfiguration()
    nodeConfig = NodeConfiguration()

    if nodeConfig.isNodeConfigured():
        if not ui.clickPrompt(
            "Node configuration already exists. Would you like to update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    node_module.configureNode(nodeConfig, verbose)
    nodeConfig.save()
    ui.previewConfig(userConfig, nodeConfig)

    ui.successEcho("Node successfully configured.")
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
