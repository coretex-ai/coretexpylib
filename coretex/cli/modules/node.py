from typing import Any, Dict, Tuple, Optional
from pathlib import Path

import os
import logging

from .utils import isGPUAvailable
from .ui import clickPrompt, arrowPrompt, highlightEcho, errorEcho, progressEcho, successEcho, stdEcho
from .node_mode import NodeMode
from ...networking import networkManager, NetworkRequestError
from ...statistics import getAvailableRamMemory
from ...configuration import loadConfig, saveConfig, isNodeConfigured
from ...utils import CommandException, docker
from ...entities.model import Model


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"
DEFAULT_STORAGE_PATH = str(Path.home() / "./coretex")
DEFAULT_RAM_MEMORY = getAvailableRamMemory()
DEFAULT_SWAP_MEMORY = DEFAULT_RAM_MEMORY * 2
DEFAULT_SHARED_MEMORY = 2
DEFAULT_NODE_MODE = NodeMode.execution


class NodeException(Exception):
    pass


def getRepository() -> str:
    return os.environ.get("CTX_NODE_IMAGE_REPO", "coretexai/coretex-node")


def pull(repository: str, tag: str) -> None:
    try:
        progressEcho("Fetching latest node version...")
        docker.imagePull(f"{repository}:{tag}")
        successEcho("Latest node version successfully fetched.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to fetch latest node version.")


def isRunning() -> bool:
    return docker.containerExists(DOCKER_CONTAINER_NAME)


def start(dockerImage: str, config: Dict[str, Any]) -> None:
    try:
        progressEcho("Starting Coretex Node...")
        docker.createNetwork(DOCKER_CONTAINER_NETWORK)

        environ = {
            "CTX_API_URL": config["serverUrl"],
            "CTX_STORAGE_PATH": config["storagePath"],
            "CTX_NODE_ACCESS_TOKEN": config["nodeAccessToken"],
            "CTX_NODE_MODE": config["nodeMode"]
        }

        modelId = config.get("modelId")
        if isinstance(modelId, int):
            environ["CTX_MODEL_ID"] = modelId

        volumes = [
            (config["storagePath"], "/root/.coretex")
        ]

        if config.get("allowDocker", False):
            volumes.append(("/var/run/docker.sock", "/var/run/docker.sock"))

        docker.start(
            DOCKER_CONTAINER_NAME,
            dockerImage,
            config["image"] == "gpu",
            config["nodeRam"],
            config["nodeSwap"],
            config["nodeSharedMemory"],
            environ,
            volumes
        )

        successEcho("Successfully started Coretex Node.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to start Coretex Node.")


def stop() -> None:
    try:
        progressEcho("Stopping Coretex Node...")

        docker.stopContainer(DOCKER_CONTAINER_NAME)
        docker.removeContainer(DOCKER_CONTAINER_NAME)
        docker.removeNetwork(DOCKER_CONTAINER_NETWORK)

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


def selectModelId(retryCount: int = 0) -> int:
    if retryCount >= 3:
        raise RuntimeError("Failed to fetch Coretex Model. Terminating...")

    modelId: int = clickPrompt("Specify Coretex Model ID that you want to use:", type = int)

    try:
        model = Model.fetchById(modelId)
    except:
        errorEcho(f"Failed to fetch model with id {modelId}.")
        return selectModelId(retryCount + 1)

    model.download()

    return modelId


def selectNodeMode() -> Tuple[int, Optional[int]]:
    availableNodeModes = {
        "Execution": NodeMode.execution,
        "Function exclusive": NodeMode.functionExclusive,
        "Function shared": NodeMode.functionShared
    }
    choices = list(availableNodeModes.keys())

    stdEcho("Please select Coretex Node mode:")
    selectedMode = arrowPrompt(choices)

    if availableNodeModes[selectedMode] == NodeMode.functionExclusive:
        modelId = selectModelId()
        return availableNodeModes[selectedMode], modelId

    return availableNodeModes[selectedMode], None


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
    config["nodeMode"] = DEFAULT_NODE_MODE
    config["allowDocker"] = False

    if verbose:
        config["storagePath"] = clickPrompt("Storage path (press enter to use default)", DEFAULT_STORAGE_PATH, type = str)
        config["nodeRam"] = clickPrompt("Node RAM memory limit in GB (press enter to use default)", DEFAULT_RAM_MEMORY, type = int)
        config["nodeSwap"] = clickPrompt("Node swap memory limit in GB, make sure it is larger than mem limit (press enter to use default)", DEFAULT_SWAP_MEMORY, type = int)
        config["nodeSharedMemory"] = clickPrompt("Node POSIX shared memory limit in GB (press enter to use default)", DEFAULT_SHARED_MEMORY, type = int)
        config["allowDocker"] = clickPrompt("Allow Node to access system docker? This is a security risk! (Y/n)", type = bool)

        nodeMode, modelId = selectNodeMode()
        config["nodeMode"] = nodeMode
        if modelId is not None:
            config["modelId"] = modelId
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
