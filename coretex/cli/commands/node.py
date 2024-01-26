import click

from ...configuration import loadConfig, CONFIG_DIR
from ..modules import node as node_module
from ..modules.update import NodeStatus, getNodeStatus, activateAutoUpdate


@click.command()
def start() -> None:
    config = loadConfig()
    dockerImage = f"coretexai/coretex-node:latest-{config['image']}"

    click.echo("Fetching latest node version.")
    node_module.pull(dockerImage)

    click.echo("Starting Coretex Node...")
    node_module.start(dockerImage, config)
    click.echo("Successfully started Coretex Node.")

    # activate auto update


@click.command()
def stop() -> None:
    click.echo("Stopping Coretex Node...")
    node_module.stop()
    click.echo("Successfully stopped Coretex Node.")


@click.command()
def update() -> None:
    config = loadConfig()
    dockerImage = f"coretexai/coretex-node:latest-{config['image']}"
    isHTTPS = True if config["isHTTPS"] else False
    activateAutoUpdate(str(CONFIG_DIR), isHTTPS)

    nodeStatus = getNodeStatus()
    if nodeStatus == NodeStatus.Active:
        click.echo("Stopping Coretex Node...")
        node_module.stop()
        click.echo("Successfully stopped Coretex Node.")

        click.echo("Fetching latest node version.")
        node_module.pull(dockerImage)

        click.echo("Starting Coretex Node...")
        node_module.start(dockerImage, config)
        click.echo("Successfully started Coretex Node.")


@click.group()
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
# node.add_command(update, "update")