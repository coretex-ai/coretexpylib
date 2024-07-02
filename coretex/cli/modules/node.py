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

from typing import Any, Dict, Optional
from enum import Enum
from pathlib import Path
from base64 import b64encode

import logging

import click

from . import config_defaults
from .utils import isGPUAvailable
from .ui import clickPrompt, arrowPrompt, highlightEcho, errorEcho, progressEcho, successEcho, stdEcho
from .node_mode import NodeMode
from ...cryptography import rsa
from ...networking import networkManager, NetworkRequestError
from ...configuration import loadConfig, saveConfig, isNodeConfigured, getInitScript
from ...utils import CommandException, docker


class NodeException(Exception):
    pass


class ImageType(Enum):

    official = "official"
    custom = "custom"


def pull(image: str) -> None:
    try:
        progressEcho(f"Fetching image {image}...")
        docker.imagePull(image)

        successEcho(f"Image {image} successfully fetched.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to fetch latest node version.")


def isRunning() -> bool:
    return docker.containerRunning(config_defaults.DOCKER_CONTAINER_NAME)


def exists() -> bool:
    return docker.containerExists(config_defaults.DOCKER_CONTAINER_NAME)


def start(dockerImage: str, config: Dict[str, Any]) -> None:
    try:
        progressEcho("Starting Coretex Node...")
        docker.createNetwork(config_defaults.DOCKER_CONTAINER_NETWORK)

        environ = {
            "CTX_API_URL": config["serverUrl"],
            "CTX_STORAGE_PATH": "/root/.coretex",
            "CTX_NODE_ACCESS_TOKEN": config["nodeAccessToken"],
            "CTX_NODE_MODE": config["nodeMode"]
        }

        nodeSecret = config.get("nodeSecret", config_defaults.DEFAULT_NODE_SECRET)
        if isinstance(nodeSecret, str) and nodeSecret != config_defaults.DEFAULT_NODE_SECRET:
            environ["CTX_NODE_SECRET"] = nodeSecret

        volumes = [
            (config["storagePath"], "/root/.coretex")
        ]

        if config.get("allowDocker", False):
            volumes.append(("/var/run/docker.sock", "/var/run/docker.sock"))

        initScript = getInitScript(config)
        if initScript is not None:
            volumes.append((str(initScript), "/script/init.sh"))

        docker.start(
            config_defaults.DOCKER_CONTAINER_NAME,
            dockerImage,
            config["allowGpu"],
            config["nodeRam"],
            config["nodeSwap"],
            config["nodeSharedMemory"],
            config["cpuCount"],
            environ,
            volumes
        )

        successEcho("Successfully started Coretex Node.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to start Coretex Node.")


def clean() -> None:
    try:
        docker.removeContainer(config_defaults.DOCKER_CONTAINER_NAME)
        docker.removeNetwork(config_defaults.DOCKER_CONTAINER_NETWORK)
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to clean inactive Coretex Node.")


def stop() -> None:
    try:
        progressEcho("Stopping Coretex Node...")
        docker.stopContainer(config_defaults.DOCKER_CONTAINER_NAME)
        clean()
        successEcho("Successfully stopped Coretex Node....")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to stop Coretex Node.")


def getRepoFromImageUrl(image: str) -> str:
    imageName = image.split("/")[-1]
    if not ":" in imageName:
        return image

    tagIndex = image.rfind(":")
    if tagIndex != -1:
        return image[:tagIndex]
    else:
        return image


def getTagFromImageUrl(image: str) -> str:
    imageName = image.split("/")[-1]
    if not ":" in imageName:
        return "latest"

    tagIndex = image.rfind(":")
    if tagIndex != -1:
        return image[tagIndex + 1:]
    else:
        return "latest"


def shouldUpdate(image: str) -> bool:
    repository = getRepoFromImageUrl(image)
    try:
        imageJson = docker.imageInspect(image)
    except CommandException:
        # imageInspect() will raise an error if image doesn't exist locally
        return True

    try:
        manifestJson = docker.manifestInspect(image)
    except CommandException:
        return False

    for digest in imageJson["RepoDigests"]:
        if repository in digest and manifestJson["Descriptor"]["digest"] in digest:
            return False

    return True


def registerNode(
    name: str,
    nodeMode: NodeMode,
    publicKey: Optional[bytes] = None,
    nearWalletId: Optional[str] = None,
    endpointInvocationPrice: Optional[float] = None
) -> str:

    params: Dict[str, Any] = {
        "machine_name": name,
        "mode": nodeMode.value
    }

    if publicKey is not None:
        params["public_key"] = b64encode(publicKey).decode("utf-8")

    if nearWalletId is not None:
        params["near_wallet_id"] = nearWalletId

    if endpointInvocationPrice is not None:
        params["endpoint_invocation_price"] = endpointInvocationPrice

    response = networkManager.post("service", params)

    if response.hasFailed():
        raise NetworkRequestError(response, "Failed to configure node. Please try again...")

    accessToken = response.getJson(dict).get("access_token")

    if not isinstance(accessToken, str):
        raise TypeError("Something went wrong. Please try again...")

    return accessToken


def selectImageType() -> ImageType:
    availableImages = {
        "Official Coretex image": ImageType.official,
        "Custom image": ImageType.custom,
    }

    choices = list(availableImages.keys())
    selectedImage = arrowPrompt(choices, "Please select image that you want to use (use arrow keys to select an option):")

    return availableImages[selectedImage]


def selectNodeMode() -> NodeMode:
    # Define modes which can be picked
    # Order of the elements in list affects how choices will
    # be displayed in the terminal
    nodeModes = [
        NodeMode.any,
        NodeMode.execution,
        NodeMode.endpointReserved,
        NodeMode.endpointShared
    ]

    availableNodeModes = { mode.toString(): mode for mode in nodeModes }
    choices = list(availableNodeModes.keys())

    selectedMode = arrowPrompt(choices, "Please select Coretex Node mode (use arrow keys to select an option):")
    return availableNodeModes[selectedMode]


def promptCpu(config: Dict[str, Any], cpuLimit: int) -> int:
    cpuCount: int = clickPrompt(f"Enter the number of CPUs the container will use (Maximum: {cpuLimit}) (press enter to use default)", cpuLimit, type = int)

    if cpuCount == 0:
        errorEcho(f"ERROR: Number of CPU's the container will use must be higher than 0")
        return promptCpu(config, cpuLimit)

    if cpuCount > cpuLimit:
        errorEcho(f"ERROR: CPU limit in Docker Desktop ({cpuLimit}) is lower than the specified value ({cpuCount})")
        return promptCpu(config, cpuLimit)

    return cpuCount


def promptRam(config: Dict[str, Any], ramLimit: int) -> int:
    nodeRam: int = clickPrompt(f"Node RAM memory limit in GB (Minimum: {config_defaults.MINIMUM_RAM}GB, Maximum: {ramLimit}GB) (press enter to use default)", ramLimit, type = int)

    if nodeRam > ramLimit:
        errorEcho(f"ERROR: RAM limit in Docker Desktop ({ramLimit}GB) is lower than the configured value ({config['nodeRam']}GB). Please adjust resource limitations in Docker Desktop settings.")
        return promptRam(config, ramLimit)

    if nodeRam < config_defaults.MINIMUM_RAM:
        errorEcho(f"ERROR: Configured RAM ({nodeRam}GB) is lower than the minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB).")
        return promptRam(config, ramLimit)

    return nodeRam


def promptSwap(nodeRam: int, swapLimit: int) -> int:
    nodeSwap: int = clickPrompt(
        f"Node SWAP memory limit in GB (Maximum: {swapLimit}GB) (press enter to use default)",
        min(swapLimit, nodeRam * 2),
        type = int
    )

    if nodeSwap > swapLimit:
        errorEcho(
            f"ERROR: SWAP memory limit in Docker Desktop ({swapLimit}GB) is lower than the configured value ({nodeSwap}GB). "
            f"If you want to use higher value than {swapLimit}GB, you have to change docker limits."
        )
        return promptSwap(nodeRam, swapLimit)

    return nodeSwap


def promptInvocationPrice() -> float:
    invocationPrice: float = clickPrompt(
        "Enter the price of a single endpoint invocation",
        config_defaults.DEFAULT_ENDPOINT_INVOCATION_PRICE,
        type = float
    )

    if invocationPrice < 0:
        errorEcho("Endpoint invocation price cannot be less than 0!")
        return promptInvocationPrice()

    return invocationPrice


def _configureInitScript() -> str:
    initScript = clickPrompt("Enter a path to sh script which will be executed before Node starts", config_defaults.DEFAULT_INIT_SCRIPT, type = str)

    if initScript == config_defaults.DEFAULT_INIT_SCRIPT:
        return config_defaults.DEFAULT_INIT_SCRIPT

    path = Path(initScript).expanduser().absolute()

    if path.is_dir():
        errorEcho("Provided path is pointing to a directory, file expected!")
        return _configureInitScript()

    if not path.exists():
        errorEcho("Provided file does not exist!")
        return _configureInitScript()

    return str(path)


def checkResourceLimitations() -> None:
    _, ramLimit = docker.getResourceLimits()

    if ramLimit < config_defaults.MINIMUM_RAM:
        raise RuntimeError(f"Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) is higher than your current Docker desktop RAM limit ({ramLimit}GB). Please adjust resource limitations in Docker Desktop settings to match Node requirements.")


def isConfigurationValid(config: Dict[str, Any]) -> bool:
    isValid = True
    cpuLimit, ramLimit = docker.getResourceLimits()
    swapLimit = docker.getDockerSwapLimit()

    if not isinstance(config["nodeRam"], int):
        errorEcho(f"Invalid config \"nodeRam\" field type \"{type(config['nodeRam'])}\". Expected: \"int\"")
        isValid = False

    if not isinstance(config["cpuCount"], int):
        errorEcho(f"Invalid config \"cpuCount\" field type \"{type(config['cpuCount'])}\". Expected: \"int\"")
        isValid = False

    if config["cpuCount"] > cpuLimit:
        errorEcho(f"Configuration not valid. CPU limit in Docker Desktop ({cpuLimit}) is lower than the configured value ({config['cpuCount']})")
        isValid = False

    if ramLimit < config_defaults.MINIMUM_RAM:
        errorEcho(f"Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) is higher than your current Docker desktop RAM limit ({ramLimit}GB). Please adjust resource limitations in Docker Desktop settings to match Node requirements.")
        isValid = False

    if config["nodeRam"] > ramLimit:
        errorEcho(f"Configuration not valid. RAM limit in Docker Desktop ({ramLimit}GB) is lower than the configured value ({config['nodeRam']}GB)")
        isValid = False

    if config["nodeSwap"] > swapLimit:
        errorEcho(f"Configuration not valid. RAM limit in Docker Desktop ({swapLimit}GB) is lower than the configured value ({config['nodeSwap']}GB)")
        isValid = False

    if config["nodeRam"] < config_defaults.MINIMUM_RAM:
        errorEcho(f"Configuration not valid. Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) is higher than the configured value ({config['nodeRam']}GB)")
        isValid = False

    return isValid


def configureNode(config: Dict[str, Any], verbose: bool) -> None:
    highlightEcho("[Node Configuration]")

    cpuLimit, ramLimit = docker.getResourceLimits()
    swapLimit = docker.getDockerSwapLimit()

    config["nodeName"] = clickPrompt("Node name", type = str)

    imageType = selectImageType()
    if imageType == ImageType.custom:
        config["image"] = clickPrompt("Specify URL of docker image that you want to use:", type = str)
    else:
        config["image"] = "coretexai/coretex-node"

    if isGPUAvailable():
        config["allowGpu"] = clickPrompt("Do you want to allow the Node to access your GPU? (Y/n)", type = bool, default = True)
    else:
        config["allowGpu"] = False

    if imageType == ImageType.official:
        tag = "gpu" if config["allowGpu"] else "cpu"
        config["image"] += f":latest-{tag}"

    config["storagePath"] = config_defaults.DEFAULT_STORAGE_PATH
    config["nodeRam"] = int(min(max(config_defaults.MINIMUM_RAM, ramLimit), config_defaults.DEFAULT_RAM))
    config["nodeSwap"] = config_defaults.DEFAULT_SWAP_MEMORY
    config["nodeSharedMemory"] = config_defaults.DEFAULT_SHARED_MEMORY
    config["cpuCount"] = int(min(cpuLimit, config_defaults.DEFAULT_CPU_COUNT))
    config["nodeMode"] = config_defaults.DEFAULT_NODE_MODE
    config["allowDocker"] = config_defaults.DEFAULT_ALLOW_DOCKER
    config["nodeSecret"] = config_defaults.DEFAULT_NODE_SECRET
    config["initScript"] = config_defaults.DEFAULT_INIT_SCRIPT

    publicKey: Optional[bytes] = None
    nearWalletId: Optional[str] = None
    endpointInvocationPrice: Optional[float] = None
    nodeMode = NodeMode.any

    if verbose:
        nodeMode = selectNodeMode()
        config["storagePath"] = clickPrompt("Storage path (press enter to use default)", config_defaults.DEFAULT_STORAGE_PATH, type = str)

        config["cpuCount"] = promptCpu(config, cpuLimit)
        config["nodeRam"] = promptRam(config, ramLimit)
        config["nodeSwap"] = promptSwap(config["nodeRam"], swapLimit)

        config["nodeSharedMemory"] = clickPrompt("Node POSIX shared memory limit in GB (press enter to use default)", config_defaults.DEFAULT_SHARED_MEMORY, type = int)
        config["allowDocker"] = clickPrompt("Allow Node to access system docker? This is a security risk! (Y/n)", config_defaults.DEFAULT_ALLOW_DOCKER, type = bool)
        config["initScript"] = _configureInitScript()

        nodeSecret: str = clickPrompt("Enter a secret which will be used to generate RSA key-pair for Node", config_defaults.DEFAULT_NODE_SECRET, type = str, hide_input = True)
        config["nodeSecret"] = nodeSecret

        if nodeSecret != config_defaults.DEFAULT_NODE_SECRET:
            progressEcho("Generating RSA key-pair (2048 bits long) using provided node secret...")
            rsaKey = rsa.generateKey(2048, nodeSecret.encode("utf-8"))
            publicKey = rsa.getPublicKeyBytes(rsaKey.public_key())

        if nodeMode in [NodeMode.endpointReserved, NodeMode.endpointShared]:
            nearWalletId = clickPrompt(
                "Enter a NEAR wallet id to which the funds will be transfered when executing endpoints",
                config_defaults.DEFAULT_NEAR_WALLET_ID,
                type = str
            )

            if nearWalletId != config_defaults.DEFAULT_NEAR_WALLET_ID:
                config["nearWalletId"] = nearWalletId
                endpointInvocationPrice = promptInvocationPrice()
            else:
                config["nearWalletId"] = None
                config["endpointInvocationPrice"] = None
                nearWalletId = None
                endpointInvocationPrice = None
    else:
        stdEcho("To configure node manually run coretex node config with --verbose flag.")

    config["nodeAccessToken"] = registerNode(config["nodeName"], nodeMode, publicKey, nearWalletId, endpointInvocationPrice)
    config["nodeMode"] = nodeMode


def initializeNodeConfiguration() -> None:
    config = loadConfig()
    isConfigured = isNodeConfigured(config)

    if isConfigured:
        if isConfigurationValid(config):
            return

        errorEcho("Invalid node configuration found.")
        if not click.confirm("Would you like to update the configuration?", default = True):
            raise RuntimeError("Invalid configuration. Please use \"coretex node config\" to update a Node configuration.")

    if not isConfigured:
        errorEcho("Node configuration not found.")

    if isRunning():
        if not click.confirm("Node is already running. Do you wish to stop the Node?", default = True):
            errorEcho("If you wish to reconfigure your node, use \"coretex node stop\" command first.")
            return

        stop()

    configureNode(config, verbose = False)
    saveConfig(config)
