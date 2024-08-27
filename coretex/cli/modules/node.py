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

from typing import Any, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path
from base64 import b64encode

import os
import logging
import requests

import click

from . import ui
from .utils import isGPUAvailable
from ...cryptography import rsa
from ...networking import networkManager, NetworkRequestError
from ...utils import CommandException, docker
from ...node import NodeMode, NodeStatus
from ...configuration import config_defaults, NodeConfiguration, InvalidConfiguration, ConfigurationNotFound


class NodeException(Exception):
    pass


class ImageType(Enum):

    official = "official"
    custom = "custom"


def pull(image: str) -> None:
    try:
        ui.progressEcho(f"Fetching image {image}...")
        docker.imagePull(image)
        ui.successEcho(f"Image {image} successfully fetched.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to fetch latest node version.")


def isRunning() -> bool:
    return docker.containerRunning(config_defaults.DOCKER_CONTAINER_NAME)


def exists() -> bool:
    return docker.containerExists(config_defaults.DOCKER_CONTAINER_NAME)


def start(dockerImage: str, nodeConfig: NodeConfiguration) -> None:
    try:
        ui.progressEcho("Starting Coretex Node...")
        docker.createNetwork(config_defaults.DOCKER_CONTAINER_NETWORK)

        environ = {
            "CTX_API_URL": os.environ["CTX_API_URL"],
            "CTX_STORAGE_PATH": "/root/.coretex",
            "CTX_NODE_ACCESS_TOKEN": nodeConfig.accessToken,
            "CTX_NODE_MODE": str(nodeConfig.mode),
            "CTX_HEARTBEAT_INTERVAL": str(nodeConfig.heartbeatInterval)
        }

        if nodeConfig.modelId is not None:
            environ["CTX_MODEL_ID"] = str(nodeConfig.modelId)

        nodeSecret = nodeConfig.secret if nodeConfig.secret is not None else config_defaults.DEFAULT_NODE_SECRET  # change in configuration
        if isinstance(nodeSecret, str) and nodeSecret != config_defaults.DEFAULT_NODE_SECRET:
            environ["CTX_NODE_SECRET"] = nodeSecret

        volumes = [
            (nodeConfig.storagePath, "/root/.coretex")
        ]

        if nodeConfig.allowDocker:
            volumes.append(("/var/run/docker.sock", "/var/run/docker.sock"))

        initScript = nodeConfig.getInitScriptPath()
        if initScript is not None:
            volumes.append((str(initScript), "/script/init.sh"))

        docker.start(
            config_defaults.DOCKER_CONTAINER_NAME,
            dockerImage,
            nodeConfig.allowGpu,
            nodeConfig.ram,
            nodeConfig.swap,
            nodeConfig.sharedMemory,
            nodeConfig.cpuCount,
            environ,
            volumes
        )

        ui.successEcho("Successfully started Coretex Node.")
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


def deactivateNode(id: Optional[int]) -> None:
    params = {
        "id": id
    }

    response = networkManager.post("service/deactivate", params)
    if response.hasFailed():
        raise NetworkRequestError(response, "Failed to deactivate node.")


def stop(nodeId: Optional[int] = None) -> None:
    try:
        ui.progressEcho("Stopping Coretex Node...")
        docker.stopContainer(config_defaults.DOCKER_CONTAINER_NAME)

        if nodeId is not None:
            deactivateNode(nodeId)

        clean()
        ui.successEcho("Successfully stopped Coretex Node....")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to stop Coretex Node.")


def getNodeStatus() -> NodeStatus:
    try:
        response = requests.get("http://localhost:21000/status", timeout = 1)
        status = response.json()["status"]
        return NodeStatus(status)
    except:
        return NodeStatus.inactive


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


def showLogs(tail: Optional[int], follow: bool, timestamps: bool) -> None:
    docker.getLogs(config_defaults.DOCKER_CONTAINER_NAME, tail, follow, timestamps)


def registerNode(
    name: str,
    nodeMode: NodeMode,
    publicKey: Optional[bytes] = None,
    nearWalletId: Optional[str] = None,
    endpointInvocationPrice: Optional[float] = None
) -> Tuple[int, str]:

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
    nodeId = response.getJson(dict).get("id")

    if not isinstance(accessToken, str) or not isinstance(nodeId, int):
        raise TypeError("Something went wrong. Please try again...")

    return nodeId, accessToken


def selectImageType() -> ImageType:
    availableImages = {
        "Official Coretex image": ImageType.official,
        "Custom image": ImageType.custom,
    }

    choices = list(availableImages.keys())
    selectedImage = ui.arrowPrompt(choices, "Please select image that you want to use (use arrow keys to select an option):")

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

    selectedMode = ui.arrowPrompt(choices, "Please select Coretex Node mode (use arrow keys to select an option):")
    return availableNodeModes[selectedMode]


def promptCpu(cpuLimit: int) -> int:
    cpuCount: int = ui.clickPrompt(f"Enter the number of CPUs the container will use (Maximum: {cpuLimit}) (press enter to use default)", cpuLimit, type = int)

    if cpuCount == 0:
        ui.errorEcho(f"ERROR: Number of CPU's the container will use must be higher than 0")
        return promptCpu(cpuLimit)

    if cpuCount > cpuLimit:
        ui.errorEcho(f"ERROR: CPU limit in Docker Desktop ({cpuLimit}) is lower than the specified value ({cpuCount})")
        return promptCpu(cpuLimit)

    return cpuCount


def promptRam(ramLimit: int) -> int:
    nodeRam: int = ui.clickPrompt(
        f"Node RAM memory limit in GB (Minimum: {config_defaults.MINIMUM_RAM}GB, "
        f"Maximum: {ramLimit}GB) (press enter to use default)",
        ramLimit,
        type = int
    )

    if nodeRam > ramLimit:
        ui.errorEcho(
            f"ERROR: RAM limit in Docker Desktop ({ramLimit}GB) is lower than the configured value ({nodeRam}GB). "
            "Please adjust resource limitations in Docker Desktop settings."
        )
        return promptRam(ramLimit)

    if nodeRam < config_defaults.MINIMUM_RAM:
        ui.errorEcho(
            f"ERROR: Configured RAM ({nodeRam}GB) is lower than "
            "the minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB)."
        )
        return promptRam(ramLimit)

    return nodeRam


def promptSwap(nodeRam: int, swapLimit: int) -> int:
    nodeSwap: int = ui.clickPrompt(
        f"Node SWAP memory limit in GB (Maximum: {swapLimit}GB) (press enter to use default)",
        min(swapLimit, nodeRam * 2),
        type = int
    )

    if nodeSwap > swapLimit:
        ui.errorEcho(
            f"ERROR: SWAP memory limit in Docker Desktop ({swapLimit}GB) is lower than the configured value ({nodeSwap}GB). "
            f"If you want to use higher value than {swapLimit}GB, you have to change docker limits."
        )
        return promptSwap(nodeRam, swapLimit)

    return nodeSwap


def promptInvocationPrice() -> float:
    invocationPrice: float = ui.clickPrompt(
        "Enter the price of a single endpoint invocation",
        config_defaults.DEFAULT_ENDPOINT_INVOCATION_PRICE,
        type = float
    )

    if invocationPrice < 0:
        ui.errorEcho("Endpoint invocation price cannot be less than 0!")
        return promptInvocationPrice()

    return invocationPrice


def _configureInitScript() -> str:
    initScript = ui.clickPrompt(
        "Enter a path to sh script which will be executed before Node starts",
        config_defaults.DEFAULT_INIT_SCRIPT,
        type = str
    )

    if initScript == config_defaults.DEFAULT_INIT_SCRIPT:
        return config_defaults.DEFAULT_INIT_SCRIPT

    path = Path(initScript).expanduser().absolute()

    if path.is_dir():
        ui.errorEcho("Provided path is pointing to a directory, file expected!")
        return _configureInitScript()

    if not path.exists():
        ui.errorEcho("Provided file does not exist!")
        return _configureInitScript()

    return str(path)


def checkResourceLimitations() -> None:
    _, ramLimit = docker.getResourceLimits()

    if ramLimit < config_defaults.MINIMUM_RAM:
        raise RuntimeError(
            f"Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) "
            "is higher than your current Docker desktop RAM limit ({ramLimit}GB). "
            "Please adjust resource limitations in Docker Desktop settings to match Node requirements."
        )


def configureNode(advanced: bool) -> NodeConfiguration:
    ui.highlightEcho("[Node Configuration]")
    nodeConfig = NodeConfiguration({})  # create new empty node config

    cpuLimit, ramLimit = docker.getResourceLimits()
    swapLimit = docker.getDockerSwapLimit()

    nodeConfig.name = ui.clickPrompt("Node name", type = str)

    imageType = selectImageType()
    if imageType == ImageType.custom:
        nodeConfig.image = ui.clickPrompt("Specify URL of docker image that you want to use:", type = str)
    else:
        nodeConfig.image = "coretexai/coretex-node"

    if isGPUAvailable():
        nodeConfig.allowGpu = ui.clickPrompt("Do you want to allow the Node to access your GPU? (Y/n)", type = bool, default = True)
    else:
        nodeConfig.allowGpu = False

    if imageType == ImageType.official:
        tag = "gpu" if nodeConfig.allowGpu else "cpu"
        nodeConfig.image += f":latest-{tag}"

    nodeConfig.storagePath = config_defaults.DEFAULT_STORAGE_PATH
    nodeConfig.ram = int(min(max(config_defaults.MINIMUM_RAM, ramLimit), config_defaults.DEFAULT_RAM))
    nodeConfig.swap = min(swapLimit, int(max(config_defaults.DEFAULT_SWAP_MEMORY, swapLimit)))
    nodeConfig.sharedMemory = config_defaults.DEFAULT_SHARED_MEMORY
    nodeConfig.cpuCount = int(min(cpuLimit, config_defaults.DEFAULT_CPU_COUNT))
    nodeConfig.mode = config_defaults.DEFAULT_NODE_MODE
    nodeConfig.allowDocker = config_defaults.DEFAULT_ALLOW_DOCKER
    nodeConfig.secret = config_defaults.DEFAULT_NODE_SECRET
    nodeConfig.initScript = config_defaults.DEFAULT_INIT_SCRIPT

    if advanced:
        nodeConfig.mode = selectNodeMode()
        nodeConfig.storagePath = ui.clickPrompt("Storage path (press enter to use default)", config_defaults.DEFAULT_STORAGE_PATH, type = str)

        nodeConfig.cpuCount = promptCpu(cpuLimit)
        nodeConfig.ram = promptRam(ramLimit)
        nodeConfig.swap = promptSwap(nodeConfig.ram, swapLimit)

        nodeConfig.sharedMemory = ui.clickPrompt(
            "Node POSIX shared memory limit in GB (press enter to use default)",
            config_defaults.DEFAULT_SHARED_MEMORY,
            type = int
        )

        nodeConfig.allowDocker = ui.clickPrompt(
            "Allow Node to access system docker? This is a security risk! (Y/n)",
            config_defaults.DEFAULT_ALLOW_DOCKER,
            type = bool
        )

        nodeConfig.initScript = _configureInitScript()

        nodeConfig.secret = ui.clickPrompt(
            "Enter a secret which will be used to generate RSA key-pair for Node",
            config_defaults.DEFAULT_NODE_SECRET,
            type = str,
            hide_input = True
        )

        if nodeConfig.mode in [NodeMode.endpointReserved, NodeMode.endpointShared]:
            nodeConfig.nearWalletId = ui.clickPrompt(
                "Enter a NEAR wallet id to which the funds will be transfered when executing endpoints",
                config_defaults.DEFAULT_NEAR_WALLET_ID,
                type = str
            )

            nodeConfig.endpointInvocationPrice = promptInvocationPrice()

        nodeConfig.heartbeatInterval = ui.clickPrompt(
            "Enter interval (seconds) at which the Node will send heartbeat to Coretex Server",
            config_defaults.HEARTBEAT_INTERVAL // 1000,
            type = int
        ) * 1000  # Node expects the value in ms
    else:
        ui.stdEcho("To configure node manually run coretex node config with --advanced flag.")

    publicKey: Optional[bytes] = None
    if nodeConfig.secret is not None and nodeConfig.secret != config_defaults.DEFAULT_NODE_SECRET:
        ui.progressEcho("Generating RSA key-pair (2048 bits long) using provided node secret...")
        rsaKey = rsa.generateKey(2048, nodeConfig.secret.encode("utf-8"))
        publicKey = rsa.getPublicKeyBytes(rsaKey.public_key())

    nodeConfig.id, nodeConfig.accessToken = registerNode(
        nodeConfig.name,
        nodeConfig.mode,
        publicKey,
        nodeConfig.nearWalletId,
        nodeConfig.endpointInvocationPrice
    )

    return nodeConfig


def initializeNodeConfiguration() -> None:
    try:
        NodeConfiguration.load()
        return
    except ConfigurationNotFound:
        ui.errorEcho("Node configuration not found.")
        if not click.confirm("Would you like to configure the node?", default = True):
            raise
    except InvalidConfiguration as ex:
        for error in ex.errors:
            ui.errorEcho(error)

        if not click.confirm("Would you like to update the configuration?", default = True):
            raise

    if isRunning():
        if not click.confirm("Node is already running. Do you wish to stop the Node?", default = True):
            ui.errorEcho("If you wish to reconfigure your node, use \"coretex node stop\" command first.")
            return

        nodeConfig = NodeConfiguration.load()
        stop(nodeConfig.id)

    nodeConfig = configureNode(advanced = False)
    nodeConfig.save()
