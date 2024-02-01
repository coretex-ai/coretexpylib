from pathlib import Path

import click

from .login import login
from ..modules import node as node_module
from ..modules.user_interface import clickPrompt, successEcho, progressEcho, highlightEcho, errorEcho, previewConfig, stdEcho
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
        if not clickPrompt(
            "Node is already running. Do you wish to restart the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        progressEcho("Stopping Coretex Node...")
        node_module.stop()
        successEcho("Successfully stopped Coretex Node.")

    if node_module.shouldUpdate(repository, tag):
        progressEcho("Fetching latest node version...")
        node_module.pull("coretexai/coretex-node", f"latest-{config['image']}")
        successEcho("Latest node version successfully fetched.")

    progressEcho("Starting Coretex Node...")
    node_module.start(f"{repository}:{tag}", config)
    successEcho("Successfully started Coretex Node.")

    activateAutoUpdate(CONFIG_DIR, config)


@click.command()
def stop() -> None:
    if not node_module.isRunning():
        errorEcho("Node is already offline.")
        return

    progressEcho("Stopping Coretex Node...")
    node_module.stop()
    successEcho("Successfully stopped Coretex Node.")


@click.command()
@onBeforeCommandExecute(node_module.initializeNodeConfiguration)
def update() -> None:
    config = loadConfig()
    repository = "coretexai/coretex-node"
    tag = f"latest-{config['image']}"

    nodeStatus = getNodeStatus()

    if nodeStatus == NodeStatus.inactive:
        errorEcho("Node is not running. To update Node you need to start it first.")
        return

    if nodeStatus == NodeStatus.reconnecting:
        errorEcho("Node is reconnecting. Cannot update now.")
        return

    if nodeStatus == NodeStatus.busy:
        if not click.prompt("Node is busy, do you wish to terminate the current execution to perform the update?? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

        progressEcho("Stopping Coretex Node...")
        node_module.stop()
        successEcho("Successfully stopped Coretex Node.")

    if not node_module.shouldUpdate(repository, tag):
        successEcho("Node is already up to date.")
        return

    progressEcho("Fetching latest node version.")
    node_module.pull(repository, tag)
    successEcho("Latest version successfully fetched.")

    progressEcho("Stopping Coretex Node...")
    node_module.stop()
    successEcho("Successfully stopped Coretex Node.")

    progressEcho("Starting Coretex Node...")
    node_module.start(f"{repository}:{tag}", config)
    successEcho("Successfully started Coretex Node.")


@click.command()
@click.option("--verbose", is_flag = True, help = "Configure node settings manually.")
def config(verbose: bool) -> None:
    if node_module.isRunning():
        if clickPrompt("Node is already running. Do you wish to stop the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False):
            node_module.stop()
        else:
            errorEcho("If you wish to reconfigure your node, use coretex node stop commands first.")
            return

    config = loadConfig()
    if not isUserConfigured(config):
        login()
        return

    if isNodeConfigured(config):
        previewConfig(config)
        if not clickPrompt(
            "Node configuration already exists. Would you like to update? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    highlightEcho("[Node Configuration]")

    config["nodeName"] = clickPrompt("Node name", type = str)
    config["nodeAccessToken"] = node_module.registerNode(config["nodeName"])

    if isGPUAvailable():
        isGPU = clickPrompt("Allow access to GPU on your node? (Y/n):", type=bool, default=True)
        config["image"] = "gpu" if isGPU else "cpu"
    else:
        config["image"] = "cpu"

    if not verbose:
        config["nodeRam"] = node_module.DEFAULT_RAM_MEMORY
        config["nodeSwap"] = node_module.DEFAULT_SWAP_MEMORY
        config["nodeSharedMemory"] = node_module.DEFAULT_SHARED_MEMORY

        stdEcho("To configure node manually run coretex node config with --verbose flag.")
    else:
        config["storagepath"] = clickPrompt("Storage path (default: ~/.coretex, press Enter to use default): ", default=Path.home() / ".coretex", type=str)
        config["nodeRam"] = clickPrompt(f"Node RAM memory limit in GB (default: {getAvailableRamMemory()}GB, press Enter to use default): ", default=getAvailableRamMemory(), type=int)
        config["nodeSwap"] = clickPrompt(f"Node swap memory limit in GB (default: {getAvailableRamMemory() * 2}GB, press Enter to use default): ", default=getAvailableRamMemory() * 2, type=int)
        config["nodeSharedMemory"] = clickPrompt("Node POSIX shared memory limit in GB (default: 2GB, press Enter to use default): ", default=2, type=int)

    saveConfig(config)
    previewConfig(config)

    # Updating auto-update script since node configuration is changed
    dumpScript(CONFIG_DIR / UPDATE_SCRIPT_NAME, config)

    successEcho("Node successfully configured.")


@click.group()
@onBeforeCommandExecute(isDockerAvailable)
@onBeforeCommandExecute(initializeUserSession)
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
node.add_command(update, "update")
node.add_command(config, "config")
