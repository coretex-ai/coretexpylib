import click

from ..configuration import loadConfig
from ..utils import CommandException
from .docker import runNode, stopNode, createNetwork


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"


@click.command()
def start() -> None:
    dockerImage = "coretexai/coretex-node:latest-cpu"
    config = loadConfig()

    try:
        createNetwork(DOCKER_CONTAINER_NETWORK)
        click.echo(f"Network {DOCKER_CONTAINER_NETWORK} successfully created.")
    except CommandException:
        click.echo(f"Failed to create network: {DOCKER_CONTAINER_NETWORK}")
        return

    try:
        runNode(
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
        click.echo(f"Node {config['nodeName']} started successfully.")
    except CommandException:
        click.echo(f"Node {config['nodeName']} failed to start.")


@click.command()
def stop() -> None:
    try:
        stopNode(DOCKER_CONTAINER_NAME, DOCKER_CONTAINER_NETWORK)
        click.echo(f"Container {DOCKER_CONTAINER_NAME} stopped successfully.")
    except CommandException:
        click.echo(f"Failed to stop container {DOCKER_CONTAINER_NAME}.")


@click.group()
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
