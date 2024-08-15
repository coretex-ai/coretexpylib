#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from importlib.metadata import version as getLibraryVersion

import sys
import click

from coretex.cli.commands.login import login
from coretex.cli.commands.model import model
from coretex.cli.commands.node import node
from coretex.cli.commands.task import run
from coretex.cli.commands.project import project

from coretex.cli.modules import ui, utils
from coretex.cli.modules.intercept import ClickExceptionInterceptor


@click.command()
def version() -> None:
    version = getLibraryVersion("coretex")
    ui.stdEcho(f"Coretex {version}")


@click.command()
def update() -> None:
    ui.stdEcho(
        "This command isn't implemented yet for compiled version but will be available soon."
        "Thanks for your patience!"
    )


@click.group(cls = ClickExceptionInterceptor)
@utils.onBeforeCommandExecute(utils.checkLibVersion, excludeSubcommands = ["update"])
def cli() -> None:
    pass

cli.add_command(login)
cli.add_command(model)
cli.add_command(project)
cli.add_command(node)
cli.add_command(run)
cli.add_command(version)
cli.add_command(update)

if getattr(sys, 'frozen', False):
    cli(sys.argv[1:])
