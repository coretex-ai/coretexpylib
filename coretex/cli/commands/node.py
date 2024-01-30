import click

from ..modules import node as node_module
from ..modules.update import NodeStatus, getNodeStatus, activateAutoUpdate
from ..modules.utils import onBeforeCommandExecute
from ..modules.docker import isDockerAvailable
from ...configuration import loadConfig, CONFIG_DIR


@click.command()
def start() -> None:
    config = loadConfig()
    dockerImage = f"coretexai/coretex-node:latest-{config['image']}"

    click.echo("Fetching latest node version...")
    node_module.pull(dockerImage)
    click.echo("Latest node version successfully fetched.")

    click.echo("Starting Coretex Node...")
    node_module.start(dockerImage, config)
    click.echo("Successfully started Coretex Node.")

    activateAutoUpdate(CONFIG_DIR, config)


@click.command()
def stop() -> None:
    click.echo("Stopping Coretex Node...")
    node_module.stop()
    click.echo("Successfully stopped Coretex Node.")


@click.command()
def update() -> None:
    config = loadConfig()
    dockerImage = f"coretexai/coretex-node:latest-{config['image']}"
    activateAutoUpdate(CONFIG_DIR, config)

    nodeStatus = getNodeStatus()
    if nodeStatus == NodeStatus.active:
        click.echo("Stopping Coretex Node...")
        node_module.stop()
        click.echo("Successfully stopped Coretex Node.")

        click.echo("Fetching latest node version.")
        node_module.pull(dockerImage)
        click.echo("Latest version successfully fetched.")

        click.echo("Starting Coretex Node...")
        node_module.start(dockerImage, config)
        click.echo("Successfully started Coretex Node.")


@click.group()
@onBeforeCommandExecute(isDockerAvailable)
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
node.add_command(update, "update")
