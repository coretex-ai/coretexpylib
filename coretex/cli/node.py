import click

from ..configuration import loadConfig
from .docker import runNode, stopNode, createNetwork


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"


@click.command()
def start() -> None:
    dockerImage = "coretexai/coretex-node:latest-cpu"
    config = loadConfig()

    createNetwork(DOCKER_CONTAINER_NETWORK)

    dockerContainerConfig = {
        "restart_policy": "always",
        "ports": "21000:21000",
        "cap_add": "SYS_PTRACE"
    }

    nodeRunning = runNode(
        DOCKER_CONTAINER_NAME,
        dockerImage,
        config["image"],
        config["serverUrl"],
        config["storagePath"],
        config["nodeAccessToken"],
        config["nodeRam"],
        config["nodeSwap"],
        config["nodeSharedMemory"],
        dockerContainerConfig["restart_policy"],
        dockerContainerConfig["ports"],
        dockerContainerConfig["cap_add"]
    )

    if nodeRunning:
        click.echo(f"Node {config['nodeName']} started successfully.")
    else:
        click.echo(f"Node {config['nodeName']} failed to start.")


@click.command()
def stop() -> None:
    success = stopNode(DOCKER_CONTAINER_NAME, DOCKER_CONTAINER_NETWORK)

    if success:
        click.echo(f"Container {DOCKER_CONTAINER_NAME} stopped successfully.")
    else:
        click.echo(f"Failed to stop container {DOCKER_CONTAINER_NAME}.")


@click.group()
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
