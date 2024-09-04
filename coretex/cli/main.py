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

import click

from .commands.base import base_group, base_command
from .commands.login import login
from .commands.model import model
from .commands.node import node
from .commands.task import task
from .commands.project import project

from .modules import ui, utils
from .modules.intercept import ClickExceptionInterceptor
from ..utils.process import CommandException


@base_command()
def version() -> None:
    version = getLibraryVersion("coretex")
    ui.stdEcho(f"Coretex {version}")


@base_command()
def update() -> None:
    currentVersion = utils.fetchCurrentVersion()
    latestVersion = utils.fetchLatestVersion()

    if currentVersion is None or latestVersion is None:
        return

    if latestVersion > currentVersion:
        try:
            ui.progressEcho("Updating coretex...")
            utils.updateLib()
            ui.successEcho(
                f"Coretex successfully updated from {utils.formatCliVersion(currentVersion)} "
                f"to {utils.formatCliVersion(latestVersion)}!"
            )
        except CommandException:
            ui.errorEcho("Failed to update coretex.")
    else:
        ui.stdEcho("Coretex version is up to date.")


@base_group(cls = ClickExceptionInterceptor, initFuncs = [(utils.checkLibVersion, ["update"])])
@click.version_option(getLibraryVersion("coretex"), "--version", "-v", message = "Coretex %(version)s")
def cli() -> None:
    pass

cli.add_command(login)
cli.add_command(model)
cli.add_command(project)
cli.add_command(node)
cli.add_command(task)
cli.add_command(version)
cli.add_command(update)
