import click

from .node import node
from .project import project
from .config import config, refresh
from .utils import makeExcludeHookGroup


refresh_decorator = makeExcludeHookGroup(refresh)

@click.group(cls = refresh_decorator())
def cli() -> None:
    pass

cli.add_command(config)
cli.add_command(project)
cli.add_command(node)
