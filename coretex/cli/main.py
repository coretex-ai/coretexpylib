import click

from .commands.login import login
from .commands.model import model
from .commands.node import node
from .commands.project import project

from .modules.intercept import ClickExceptionInterceptor


@click.group(cls = ClickExceptionInterceptor)
def cli() -> None:
    pass

cli.add_command(login)
cli.add_command(model)
cli.add_command(project)
cli.add_command(node)
