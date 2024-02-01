from typing import Any, Dict
from pathlib import Path

import logging

import click

from . import docker

from .utils import isGPUAvailable
from ...networking import networkManager
from ...statistics import getAvailableRamMemory
from ...configuration import loadConfig, saveConfig, isNodeConfigured


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"
DEFAULT_RAM_MEMORY = getAvailableRamMemory()
DEFAULT_SWAP_MEMORY = DEFAULT_RAM_MEMORY * 2
DEFAULT_SHARED_MEMORY = 2


class NodeException(Exception):
    pass


def pull(repository: str, tag: str) -> None:
    try:
        docker.imagePull(f"{repository}:{tag}")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to fetch latest node version")


def isRunning() -> bool:
    return docker.containerExists(DOCKER_CONTAINER_NAME)


def start(dockerImage: str, config: Dict[str, Any]) -> None:
    try:
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
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to start Coretex Node.")


def stop() -> None:
    try:
        docker.stop(DOCKER_CONTAINER_NAME, DOCKER_CONTAINER_NETWORK)
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
    except:
        return False


def registerNode(name: str) -> str:
    params = {
        "machine_name": name
    }
    response = networkManager.post("service", params)

    if response.hasFailed():
        raise Exception("Failed to configure node. Please try again...")

    accessToken = response.getJson(dict).get("access_token")

    if not isinstance(accessToken, str):
        raise TypeError("Something went wrong. Please try again...")

    return accessToken


def initializeNodeConfiguration() -> None:
    config = loadConfig()
    if not isNodeConfigured(config):
        click.echo("Node configuration not found.")
        click.echo("[Node Configuration]")

        config["nodeName"] = click.prompt("Node name", type = str)
        config["nodeAccessToken"] = registerNode(config["nodeName"])

        if isGPUAvailable():
            isGPU = click.prompt("Would you like to allow access to GPU on your node (Y/n)?", type = bool, default = True)
            config["image"] = "gpu" if isGPU else "cpu"
        else:
            config["image"] = "cpu"

        config["nodeRam"] = DEFAULT_RAM_MEMORY
        config["nodeSwap"] = DEFAULT_SWAP_MEMORY
        config["nodeSharedMemory"] = DEFAULT_SHARED_MEMORY

        saveConfig(config)
