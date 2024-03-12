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

from typing import Any, Dict, Tuple, Optional
from enum import Enum
from pathlib import Path

import logging

from . import config_defaults
from .utils import isGPUAvailable
from .ui import clickPrompt, arrowPrompt, highlightEcho, errorEcho, progressEcho, successEcho, stdEcho
from .node_mode import NodeMode
from ...networking import networkManager, NetworkRequestError
from ...configuration import loadConfig, saveConfig, isNodeConfigured, getInitScript
from ...utils import CommandException, docker
from ...entities.model import Model


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

        modelId = config.get("modelId")
        if isinstance(modelId, int):
            environ["CTX_MODEL_ID"] = modelId

        secretsKey = config.get("secretsKey", config_defaults.DEFAULT_SECRETS_KEY)
        if isinstance(secretsKey, str) and secretsKey != config_defaults.DEFAULT_SECRETS_KEY:
            environ["CTX_SECRETS_KEY"] = secretsKey

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


def selectImageType() -> ImageType:
    availableImages = {
        "Official Coretex image": ImageType.official,
        "Custom image": ImageType.custom,
    }

    choices = list(availableImages.keys())
    selectedImage = arrowPrompt(choices, "Please select image that you want to use (use arrow keys to select an option):")

    return availableImages[selectedImage]


def selectModelId(storagePath: str, retryCount: int = 0) -> int:
    if retryCount >= 3:
        raise RuntimeError("Failed to fetch Coretex Model. Terminating...")

    modelId: int = clickPrompt("Specify Coretex Model ID that you want to use:", type = int)

    try:
        model = Model.fetchById(modelId)
    except:
        errorEcho(f"Failed to fetch model with id {modelId}.")
        return selectModelId(storagePath, retryCount + 1)

    modelDir = Path(storagePath) / "models"
    modelDir.mkdir(parents = True, exist_ok = True)
    model.download(modelDir / str(model.id))

    return modelId


def selectNodeMode(storagePath: str) -> Tuple[int, Optional[int]]:
    availableNodeModes = {
        "Run workflows (worker)": NodeMode.execution,
        "Serve a single endpoint (dedicated inference)": NodeMode.functionExclusive,
        "Serve multiple endpoints (shared inference)": NodeMode.functionShared
    }
    choices = list(availableNodeModes.keys())

    selectedMode = arrowPrompt(choices, "Please select Coretex Node mode (use arrow keys to select an option):")

    if availableNodeModes[selectedMode] == NodeMode.functionExclusive:
        modelId = selectModelId(storagePath)
        return availableNodeModes[selectedMode], modelId

    return availableNodeModes[selectedMode], None


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


def configureNode(config: Dict[str, Any], verbose: bool) -> None:
    highlightEcho("[Node Configuration]")
    config["nodeName"] = clickPrompt("Node name", type = str)
    config["nodeAccessToken"] = registerNode(config["nodeName"])

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
    config["nodeRam"] = config_defaults.DEFAULT_RAM_MEMORY
    config["nodeSwap"] = config_defaults.DEFAULT_SWAP_MEMORY
    config["nodeSharedMemory"] = config_defaults.DEFAULT_SHARED_MEMORY
    config["cpuCount"] = config_defaults.DEFAULT_CPU_COUNT
    config["nodeMode"] = config_defaults.DEFAULT_NODE_MODE
    config["allowDocker"] = config_defaults.DEFAULT_ALLOW_DOCKER
    config["secretsKey"] = config_defaults.DEFAULT_SECRETS_KEY
    config["initScript"] = config_defaults.DEFAULT_INIT_SCRIPT

    if verbose:
        config["storagePath"] = clickPrompt("Storage path (press enter to use default)", config_defaults.DEFAULT_STORAGE_PATH, type = str)
        config["nodeRam"] = clickPrompt("Node RAM memory limit in GB (press enter to use default)", config_defaults.DEFAULT_RAM_MEMORY, type = int)
        config["nodeSwap"] = clickPrompt("Node swap memory limit in GB, make sure it is larger than mem limit (press enter to use default)", config_defaults.DEFAULT_SWAP_MEMORY, type = int)
        config["nodeSharedMemory"] = clickPrompt("Node POSIX shared memory limit in GB (press enter to use default)", config_defaults.DEFAULT_SHARED_MEMORY, type = int)
        config["cpuCount"] = clickPrompt("Enter the number of CPUs the container will use (press enter to use default)", config_defaults.DEFAULT_CPU_COUNT, type = int)
        config["allowDocker"] = clickPrompt("Allow Node to access system docker? This is a security risk! (Y/n)", config_defaults.DEFAULT_ALLOW_DOCKER, type = bool)
        config["secretsKey"] = clickPrompt("Enter a key used for decrypting your Coretex Secrets", config_defaults.DEFAULT_SECRETS_KEY, type = str, hide_input = True)
        config["initScript"] = _configureInitScript()

        nodeMode, modelId = selectNodeMode(config["storagePath"])
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
