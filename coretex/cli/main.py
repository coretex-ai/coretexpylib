import click

from .node import node
from .project import project
from .config import config


@click.group()
def cli() -> None:
    pass

cli.add_command(config)
cli.add_command(project)
cli.add_command(node)
