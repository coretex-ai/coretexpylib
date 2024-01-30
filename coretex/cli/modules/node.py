from typing import Any, Dict

import logging

from . import docker


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"


class NodeException(Exception):
    pass


def pull(repository: str, tag: str) -> None:
    try:
        docker.imagePull(f"{repository}:{tag}")
    except BaseException as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise NodeException("Failed to fetch latest node version")


def start(dockerImage: str, config: Dict[str, Any]) -> None:
    dockerImage = f"coretexai/coretex-node:latest-{config['image']}"

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
            if repository in digest:
                if manifestJson["Descriptor"]["digest"] in digest:
                    return False
        return True
    except:
        return False