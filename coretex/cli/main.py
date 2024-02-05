import click

from .commands.node import node
from .commands.project import project
from .commands.login import login

@click.group()
def cli() -> None:
    pass

cli.add_command(project)
cli.add_command(node)
cli.add_command(login)
