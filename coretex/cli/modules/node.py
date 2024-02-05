from typing import Any, Dict
from pathlib import Path

import logging

from . import docker
from .utils import isGPUAvailable
from .ui import clickPrompt, highlightEcho, errorEcho, progressEcho, successEcho, stdEcho
from ...networking import networkManager, NetworkRequestError
from ...statistics import getAvailableRamMemory
from ...configuration import loadConfig, saveConfig, isNodeConfigured
from ...utils import CommandException


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"
DEFAULT_STORAGE_PATH = str(Path.home() / "./coretex")
DEFAULT_RAM_MEMORY = getAvailableRamMemory()
DEFAULT_SWAP_MEMORY = DEFAULT_RAM_MEMORY * 2
DEFAULT_SHARED_MEMORY = 2


class NodeException(Exception):
    pass


def pull(repository: str, tag: str) -> None:
    try:
        progressEcho("Fetching latest node version...")
        docker.imagePull(f"{repository}:{tag}")
        successEcho("Latest node version successfully fetched.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to fetch latest node version")


def isRunning() -> bool:
    return docker.containerExists(DOCKER_CONTAINER_NAME)


def start(dockerImage: str, config: Dict[str, Any]) -> None:
    try:
        progressEcho("Starting Coretex Node...")
        docker.createNetwork(DOCKER_CONTAINER_NETWORK)

        docker.start(
            DOCKER_CONTAINER_NAME,
            dockerImage,
            config["image"],
            config["serverUrl"],
            config["storagePath"],
            config["nodeAccessToken"],
            config["nodeRam"],
            config["nodeSwap"],
            config["nodeSharedMemory"]
        )
        successEcho("Successfully started Coretex Node.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to start Coretex Node.")


def stop() -> None:
    try:
        progressEcho("Stopping Coretex Node...")
        docker.stop(DOCKER_CONTAINER_NAME, DOCKER_CONTAINER_NETWORK)
        successEcho("Successfully stopped Coretex Node.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to stop Coretex Node.")


def shouldUpdate(repository: str, tag: str) -> bool:
    try:
        imageJson = docker.imageInspect(repository, tag)
    except CommandException:
        # imageInspect() will raise an error if image doesn't exist locally
        return True

    try:
        manifestJson = docker.manifestInspect(repository, tag)
    except CommandException:
        return False

    for digest in imageJson["RepoDigests"]:
        if repository in digest and manifestJson["Descriptor"]["digest"] in digest:
            return False

    return True


def registerNode(name: str) -> str:
    response = networkManager.post("service", {
        "machine_name": name,
    })

    if response.hasFailed():
        raise NetworkRequestError(response, "Failed to configure node. Please try again...")

    accessToken = response.getJson(dict).get("access_token")

    if not isinstance(accessToken, str):
        raise TypeError("Something went wrong. Please try again...")

    return accessToken


def configureNode(config: Dict[str, Any], verbose: bool) -> None:
    highlightEcho("[Node Configuration]")
    config["nodeName"] = clickPrompt("Node name", type = str)
    config["nodeAccessToken"] = registerNode(config["nodeName"])

    if isGPUAvailable():
        isGPU = clickPrompt("Do you want to allow the Node to access your GPU? (Y/n)", type = bool, default = True)
        config["image"] = "gpu" if isGPU else "cpu"
    else:
        config["image"] = "cpu"

    config["storagePath"] = DEFAULT_STORAGE_PATH
    config["nodeRam"] = DEFAULT_RAM_MEMORY
    config["nodeSwap"] = DEFAULT_SWAP_MEMORY
    config["nodeSharedMemory"] = DEFAULT_SHARED_MEMORY

    if verbose:
        config["storagePath"] = clickPrompt("Storage path (press enter to use default)", DEFAULT_STORAGE_PATH, type = str)
        config["nodeRam"] = clickPrompt("Node RAM memory limit in GB (press enter to use default)", type = int, default = DEFAULT_RAM_MEMORY)
        config["nodeSwap"] = clickPrompt("Node swap memory limit in GB, make sure it is larger than mem limit (press enter to use default)", type = int, default = DEFAULT_SWAP_MEMORY)
        config["nodeSharedMemory"] = clickPrompt("Node POSIX shared memory limit in GB (press enter to use default)", type = int, default = DEFAULT_SHARED_MEMORY)
    else:
        stdEcho("To configure node manually run coretex node config with --verbose flag.")


def initializeNodeConfiguration() -> None:
    config = loadConfig()

    if isNodeConfigured(config):
        return

    errorEcho("Node configuration not found.")
    if isRunning():
        stopNode = clickPrompt(
            "Node is already running. Do you wish to stop the Node? (Y/n)",
            type = bool,
            default = True,
            show_default = False
        )

        if not stopNode:
            errorEcho("If you wish to reconfigure your node, use \"coretex node stop\" command first.")
            return

        stop()

    configureNode(config, verbose = False)
    saveConfig(config)
