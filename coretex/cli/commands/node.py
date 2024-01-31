import click

from ..modules import node as node_module
from ..modules.update import NodeStatus, getNodeStatus, activateAutoUpdate
from ..modules.utils import onBeforeCommandExecute
from ..modules.docker import isDockerAvailable
from ...configuration import loadConfig, CONFIG_DIR


@click.command()
def start() -> None:
    config = loadConfig()
    repository = "coretexai/coretex-node"
    tag = f"latest-{config['image']}"

    if node_module.isRunning():
        if not click.prompt(
            "Node is already running do you wish to restart node (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    if node_module.shouldUpdate(repository, tag):
        click.echo("Fetching latest node version...")
        node_module.pull("coretexai/coretex-node", f"latest-{config['image']}")
        click.echo("Latest node version successfully fetched.")

    click.echo("Starting Coretex Node...")
    node_module.start(f"{repository}:{tag}", config)
    click.echo("Successfully started Coretex Node.")

    activateAutoUpdate(CONFIG_DIR, config)


@click.command()
def stop() -> None:
    if not node_module.isRunning():
        click.echo("Node is already offline.")
        return

    click.echo("Stopping Coretex Node...")
    node_module.stop()
    click.echo("Successfully stopped Coretex Node.")


@click.command()
def update() -> None:
    config = loadConfig()
    repository = "coretexai/coretex-node"
    tag = f"latest-{config['image']}"

    if getNodeStatus() != NodeStatus.active:
        click.echo("Node status is inactive. Make sure node is up and running.")
        return

    if not node_module.shouldUpdate(repository, tag):
        click.echo("Node version is up to date.")
        return

    click.echo("Fetching latest node version.")
    node_module.pull(repository, tag)
    click.echo("Latest version successfully fetched.")

    click.echo("Stopping Coretex Node...")
    node_module.stop()
    click.echo("Successfully stopped Coretex Node.")

    click.echo("Starting Coretex Node...")
    node_module.start(f"{repository}:{tag}", config)
    click.echo("Successfully started Coretex Node.")


@click.group()
@onBeforeCommandExecute(isDockerAvailable)
def node() -> None:
    pass


node.add_command(start, "start")
node.add_command(stop, "stop")
node.add_command(update, "update")
