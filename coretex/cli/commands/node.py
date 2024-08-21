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
from pathlib import Path

import click

from ..modules import ui
from ..modules import node as node_module
from ..modules.node import NodeStatus
from ..modules.user import initializeUserSession
from ..modules.utils import onBeforeCommandExecute, checkEnvironment
from ..modules.update import activateAutoUpdate, getNodeStatus
from ...utils import docker
from ...configuration import NodeConfiguration, InvalidConfiguration, ConfigurationNotFound


@click.command()
@click.option("--image", type = str, help = "Docker image url")
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def start(image: Optional[str]) -> None:
    nodeConfig = NodeConfiguration.load()

    if node_module.isRunning():
        if not ui.clickPrompt(
            "Node is already running. Do you wish to restart the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop(nodeConfig.id)

    if node_module.exists():
        node_module.clean()


    if image is not None:
        nodeConfig.image = image  # store forced image (flagged) so we can run autoupdate afterwards
        nodeConfig.save()

    dockerImage = nodeConfig.image

    if node_module.shouldUpdate(dockerImage):
        node_module.pull(dockerImage)

    node_module.start(dockerImage, nodeConfig)
    docker.removeDanglingImages(node_module.getRepoFromImageUrl(dockerImage), node_module.getTagFromImageUrl(dockerImage))
    activateAutoUpdate()


@click.command()
def stop() -> None:
    nodeConfig = NodeConfiguration.load()

    if not node_module.isRunning():
        ui.errorEcho("Node is already offline.")
        return

    node_module.stop(nodeConfig.id)


@click.command()
@click.option("-y", "autoAccept", is_flag = True, help = "Accepts all prompts.")
@click.option("-n", "autoDecline", is_flag = True, help = "Declines all prompts.")
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def update(autoAccept: bool, autoDecline: bool) -> None:
    if autoAccept and autoDecline:
        ui.errorEcho("Only one of the flags (\"-y\" or \"-n\") can be used at the same time.")
        return

    nodeConfig = NodeConfiguration.load()
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

        node_module.stop(nodeConfig.id)

    if not node_module.shouldUpdate(nodeConfig.image):
        ui.successEcho("Node is already up to date.")
        return

    ui.stdEcho("Fetching latest node image...")
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

    node_module.stop(nodeConfig.id)

    ui.stdEcho("Updating node...")
    node_module.start(nodeConfig.image, nodeConfig)

    docker.removeDanglingImages(
        node_module.getRepoFromImageUrl(nodeConfig.image),
        node_module.getTagFromImageUrl(nodeConfig.image)
    )
    activateAutoUpdate()


@click.command()
@click.option("--advanced", is_flag = True, help = "Configure node settings manually.")
def config(advanced: bool) -> None:
    if node_module.isRunning():
        if not ui.clickPrompt(
            "Node is already running. Do you wish to stop the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            ui.errorEcho("If you wish to reconfigure your node, use coretex node stop commands first.")
            return

        try:
            nodeConfig = NodeConfiguration.load()
            node_module.stop(nodeConfig.id)
        except (ConfigurationNotFound, InvalidConfiguration):
            node_module.stop()

    try:
        nodeConfig = NodeConfiguration.load()
        if not ui.clickPrompt(
            "Node configuration already exists. Would you like to update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return
    except (ConfigurationNotFound, InvalidConfiguration):
        pass

    nodeConfig = node_module.configureNode(advanced)
    nodeConfig.save()
    ui.previewNodeConfig(nodeConfig)

    ui.successEcho("Node successfully configured.")
    activateAutoUpdate()


@click.command()
def status() -> None:
    nodeStatus = getNodeStatus()
    statusColors = {
        "inactive": "red",
        "active": 'green',
        "busy": "cyan",
        "reconnecting": "yellow"
    }

    statusEcho = click.style(nodeStatus.name, fg = statusColors[nodeStatus.name])
    ui.stdEcho(f"Current status of node is {statusEcho}.")


@click.command()
@click.option("--tail", "-n", type = int, help = "Shows N last logs.")
@click.option("--follow", "-f", is_flag = True, help = "Displays logs realtime.")
@click.option("--timestamps", "-t", is_flag = True, help = "Displays timestamps for logs.")
def logs(tail: Optional[int], follow: bool, timestamps: bool) -> None:
    if not node_module.isRunning():
        ui.errorEcho("There is no currently running Node on the machine.")
        return

    node_module.showLogs(tail, follow, timestamps)


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
node.add_command(status, "status")
node.add_command(logs, "logs")
