import click

from .config import config
from .project import project

@click.group()
def cli() -> None:
    pass

cli.add_command(config)
cli.add_command(project)
