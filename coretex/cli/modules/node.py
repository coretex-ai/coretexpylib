from typing import Any, Dict

import logging

import click

from .user_interface import clickPrompt

from . import docker

from .utils import isGPUAvailable
from .user_interface import highlightEcho, errorEcho, progressEcho, successEcho
from ...networking import networkManager
from ...statistics import getAvailableRamMemory
from ...configuration import loadConfig, saveConfig, isNodeConfigured
from ...utils import CommandException


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"
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
        progressEcho("Starting Coretex Node...")
        docker.stop(DOCKER_CONTAINER_NAME, DOCKER_CONTAINER_NETWORK)
        successEcho("Successfully started Coretex Node.")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to stop Coretex Node.")


def shouldUpdate(repository: str, tag: str) -> bool:
    try:
        imageJson = docker.imageInspect(repository, tag)
        manifestJson = docker.manifestInspect(repository, tag)

        for digest in imageJson["RepoDigests"]:
            if repository in digest and manifestJson["Descriptor"]["digest"] in digest:
                return False
        return True
    except CommandException:
        return True


def registerNode(name: str) -> str:
    params = {
        "machine_name": name
    }
    response = networkManager.post("service", params)

    if response.hasFailed():
        print(response.getJson(dict))
        raise Exception("Failed to configure node. Please try again...")

    accessToken = response.getJson(dict).get("access_token")

    if not isinstance(accessToken, str):
        raise TypeError("Something went wrong. Please try again...")

    return accessToken


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
            errorEcho("If you wish to reconfigure your node, use coretex node stop commands first.")
            return

        stop()

    highlightEcho("[Node Configuration]")
    config["nodeName"] = clickPrompt("Node name", type = str)
    config["nodeAccessToken"] = registerNode(config["nodeName"])

    if isGPUAvailable():
        isGPU = clickPrompt("Would you like to allow access to GPU on your node? (Y/n)", type = bool, default = True)
        config["image"] = "gpu" if isGPU else "cpu"
    else:
        config["image"] = "cpu"

    config["nodeRam"] = DEFAULT_RAM_MEMORY
    config["nodeSwap"] = DEFAULT_SWAP_MEMORY
    config["nodeSharedMemory"] = DEFAULT_SHARED_MEMORY

    saveConfig(config)
