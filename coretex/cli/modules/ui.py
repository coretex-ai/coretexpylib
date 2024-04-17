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

from typing import Any, List, Optional, Union

from tabulate import tabulate

import click
import inquirer

from ...entities import NodeMode
from ...configuration import UserConfiguration, NodeConfiguration


def clickPrompt(
    text: str,
    default: Any = None,
    type: Optional[Union[type, click.ParamType]] = None,
    **kwargs: Any
) -> Any:

    return click.prompt(click.style(f"\n\U00002754 {text}", fg = "cyan"), default = default, type = type, **kwargs)


def arrowPrompt(choices: List[Any], message: str) -> Any:
    click.echo("\n")
    answers = inquirer.prompt([
        inquirer.List(
            "option",
            message = message,
            choices = choices,
        )
    ])

    return answers["option"]


def previewConfig(userConfig: UserConfiguration, nodeConfig: NodeConfiguration) -> None:
    allowDocker = "Yes" if nodeConfig.allowDocker else "No"

    if nodeConfig.nodeSecret is None or nodeConfig.nodeSecret == "":
        nodeSecret = ""
    else:
        nodeSecret = "********"

    table = [
        ["Node name",           nodeConfig.nodeName],
        ["Server URL",          userConfig.serverUrl],
        ["Coretex Node type",   nodeConfig.image],
        ["Storage path",        nodeConfig.storagePath],
        ["RAM",                 f"{nodeConfig.nodeRam}GB"],
        ["SWAP memory",         f"{nodeConfig.nodeSwap}GB"],
        ["POSIX shared memory", f"{nodeConfig.nodeSharedMemory}GB"],
        ["CPU cores allocated", f"{nodeConfig.cpuCount}"],
        ["Coretex Node mode",   f"{NodeMode(nodeConfig.nodeMode).name}"],
        ["Docker access",       allowDocker],
        ["Coretex Node secret",         nodeSecret],
        ["Coretex Node init script",    nodeConfig.initScript if nodeConfig.initScript is not None else ""]
    ]
    if nodeConfig.modelId is not None:
        table.append(["Coretex Model ID", f"{nodeConfig.modelId}"])

    stdEcho(tabulate(table))


def outputUrl(entityUrl: str) -> str:
    return f"https://app.coretex.ai/{entityUrl}"


def stdEcho(text: str) -> None:
    click.echo(click.style(f"\n{text}", fg = "cyan"))


def successEcho(text: str) -> None:
    click.echo(click.style(f"\n\U0001F680 {text} \U0001F680", fg = "green"))


def progressEcho(text: str) -> None:
    click.echo(click.style(f"\n\U00002699 {text} \U00002699", fg = "yellow"))


def errorEcho(text: str) -> None:
    click.echo(click.style(f"\n\U0000274C {text} \U0000274C", fg = "red"))


def highlightEcho(text: str) -> None:
    click.echo(click.style(f"\n\U00002755 {text} \U00002755"))
