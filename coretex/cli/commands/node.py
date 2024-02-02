from pathlib import Path

import click

from .login import login
from ..modules import node as node_module
from ..modules.update import NodeStatus, getNodeStatus, activateAutoUpdate, dumpScript, UPDATE_SCRIPT_NAME
from ..modules.utils import onBeforeCommandExecute, isGPUAvailable
from ..modules.user import initializeUserSession
from ..modules.docker import isDockerAvailable
from ...configuration import loadConfig, saveConfig, CONFIG_DIR, isUserConfigured, isNodeConfigured
from ...statistics import getAvailableRamMemory


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
            show_default = False):
            node_module.stop()

        click.echo("If you wish to reconfigure your node, use coretex node stop commands first.")
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

    config["storagepath"] = Path.home() / ".coretex"
    config["nodeName"] = click.prompt("Node name", type = str)
    config["nodeAccessToken"] = node_module.registerNode(config["nodeName"])

    if isGPUAvailable():
        isGPU = click.prompt("Would you like to allow access to GPU on your node? (Y/n)", type = bool, default = True)
        config["image"] = "gpu" if isGPU else "cpu"
    else:
        config["image"] = "cpu"

    if not verbose:
        config["nodeRam"] = node_module.DEFAULT_RAM_MEMORY
        config["nodeSwap"] = node_module.DEFAULT_SWAP_MEMORY
        config["nodeSharedMemory"] = node_module.DEFAULT_SHARED_MEMORY

        click.echo("To configure node manually run coretex node config with --verbose flag.")
    else:
        config["storagepath"] = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)
        config["nodeRam"] = click.prompt("Node RAM memory limit in GB (press enter to use default)", type = int, default = getAvailableRamMemory())
        config["nodeSwap"] = click.prompt("Node swap memory limit in GB, make sure it is larger then mem limit (press enter to use default)", type = int, default = getAvailableRamMemory() * 2)
        config["nodeSharedMemory"] = click.prompt("Node POSIX shared memory limit in GB (press enter to use default)", type = int, default = 2)

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
