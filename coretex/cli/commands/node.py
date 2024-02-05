from pathlib import Path

import click

from ..modules import node as node_module
from ..modules.update import NodeStatus, getNodeStatus, activateAutoUpdate, dumpScript, UPDATE_SCRIPT_NAME
from ..modules.utils import onBeforeCommandExecute
from ..modules.user import initializeUserSession
from ..modules.docker import isDockerAvailable
from ...configuration import loadConfig, saveConfig, CONFIG_DIR, isNodeConfigured


@click.command()
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def start() -> None:
    config = loadConfig()
    repository = "coretexai/coretex-node"
    tag = f"latest-{config['image']}"

    if node_module.isRunning():
        if not click.prompt(
            "Node is already running. Do you wish to restart the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop()

    if node_module.shouldUpdate(repository, tag):
        node_module.pull("coretexai/coretex-node", f"latest-{config['image']}")

    node_module.start(f"{repository}:{tag}", config)

    activateAutoUpdate(CONFIG_DIR, config)


@click.command()
def stop() -> None:
    if not node_module.isRunning():
        click.echo("Node is already offline.")
        return

    node_module.stop()


@click.command()
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def update() -> None:
    config = loadConfig()
    repository = "coretexai/coretex-node"
    tag = f"latest-{config['image']}"

    nodeStatus = getNodeStatus()

    if nodeStatus == NodeStatus.inactive:
        click.echo("Node is not running. To update Node you need to start it first.")
        return

    if nodeStatus == NodeStatus.reconnecting:
        click.echo("Node is reconnecting. Cannot update now.")
        return

    if nodeStatus == NodeStatus.busy:
        if not click.prompt("Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        node_module.stop()

    if not node_module.shouldUpdate(repository, tag):
        click.echo("Node is already up to date.")
        return

    node_module.pull(repository, tag)

    if getNodeStatus() == NodeStatus.busy:
        if not click.prompt("Node is busy, do you wish to terminate the current execution to perform the update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    node_module.stop()

    node_module.start(f"{repository}:{tag}", config)


@click.command()
@click.option("--verbose", is_flag = True, help = "Configure node settings manually.")
def config(verbose: bool) -> None:
    if node_module.isRunning():
        if click.prompt("Node is already running. Do you wish to stop the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            node_module.stop()

        click.echo("If you wish to reconfigure your node, use \"coretex node stop\" command first.")
        return

    config = loadConfig()

    if isNodeConfigured(config):
        if not click.prompt(
            "Node configuration already exists. Would you like to update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    click.echo("[Node Configuration]")
    node_module.configureNode(config, verbose)
    saveConfig(config)

    # Updating auto-update script since node configuration is changed
    dumpScript(CONFIG_DIR / UPDATE_SCRIPT_NAME, config)

    click.echo("Node successfully configured.")


@click.group()
@onBeforeCommandExecute(isDockerAvailable)
@onBeforeCommandExecute(initializeUserSession)
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
node.add_command(update, "update")
node.add_command(config, "config")
