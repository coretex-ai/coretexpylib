from typing import Dict
from docker.errors import DockerException, NotFound, APIError

import click
import docker

from ..configuration import loadConfig


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"


@click.command()
def start() -> None:
    try:
        client = docker.from_env()
    except DockerException:
        click.echo("Please make sure you have docker installed on your machine and it is up and running. If that's the case (troubleshoot?)")
        return

    config = loadConfig()

    dockerImage = client.images.pull("coretexai/coretex-node:latest-cpu")
    dockerContainerConfig = {
        "name": DOCKER_CONTAINER_NAME,
        "environment": {
            "CTX_API_URL": config["serverUrl"],
            "CTX_STORAGE_PATH": config["storagePath"],
            "CTX_NODE_ACCESS_TOKEN": config["nodeAccessToken"]
        },
        "restart_policy": {
            "Name": "always"
        },
        "ports": {
            "21000": "21000"
        },
        "cap_add": [
            "SYS_PTRACE"
        ],
        "network": DOCKER_CONTAINER_NETWORK,
        "mem_limit": config["nodeRam"],
        "memswap_limit": config["nodeSwap"],
        "shm_size": config["nodeSharedMemory"]
    }

    if config["image"] == "gpu":
        dockerContainerConfig["runtime"] = "nvidia"

    try:
        client.networks.create(dockerContainerConfig["network"], driver = "bridge")
        click.echo(f"Successfully created {dockerContainerConfig['network']} network for container.")
    except APIError as e:
        click.echo(f"Error while creating {dockerContainerConfig['network']} network for container.")
        return

    container = client.containers.run(detach = True, image = dockerImage,  **dockerContainerConfig)
    if container is not None:
        click.echo(f"Node with name {container.name} started successfully.")
    else:
        click.echo("Failed to start container.")


@click.command()
def stop() -> None:
    client = docker.from_env()
    try:
        network = client.networks.get(DOCKER_CONTAINER_NETWORK)
        container = client.containers.get(DOCKER_CONTAINER_NAME)

        network.disconnect(container)
        container.stop()

        network.remove()
        container.remove()

        click.echo(f"Container {DOCKER_CONTAINER_NAME} stopped successfully.")
    except NotFound:
        click.echo(f"Container {DOCKER_CONTAINER_NAME} not found.")
    except APIError:
        click.echo(f"Error occurred while stopping container {DOCKER_CONTAINER_NAME}.")


@click.group()
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
