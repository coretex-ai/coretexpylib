from typing import Any, List, Dict, Optional

from tabulate import tabulate

import click
import inquirer

from .node_mode import NodeMode


def clickPrompt(text: str, default: Any = None, type: Optional[type] = None, **kwargs: Any) -> Any:
    return click.prompt(click.style(text, fg = "blue"), default = default, type = type, **kwargs)


def arrowPrompt(choices: List[Any]) -> Any:
    answers = inquirer.prompt([
        inquirer.List(
            "option",
            message = "Use arrow keys to select an option",
            choices = choices,
            carousel = True,
        )
    ])

    return answers["option"]


def previewConfig(config: Dict[str, Any]) -> None:
    table = [
        ["Node name", config["nodeName"]],
        ["Server URL", config["serverUrl"]],
        ["Coretex Node type", config["image"]],
        ["Storage path", config["storagePath"]],
        ["RAM", f"{config['nodeRam']}GB"],
        ["SWAP memory", f"{config['nodeSwap']}GB"],
        ["POSIX shared memory", f"{config['nodeSharedMemory']}GB"],
        ["Coretex Node mode", f"{NodeMode(config['nodeMode']).name}"],
        ["Docker access", "Yes" if config.get("allowDocker", False) else "No"]
    ]
    if config.get("modelId") is not None:
        table.append(["Coretex Model ID", config["modelId"]])

    stdEcho(tabulate(table, tablefmt = "grid"))


def stdEcho(text: str) -> None:
    click.echo(click.style(text, fg = "blue"))


def successEcho(text: str) -> None:
    click.echo(click.style(text, fg = "green"))


def progressEcho(text: str) -> None:
    click.echo(click.style(text, fg = "yellow"))


def errorEcho(text: str) -> None:
    click.echo(click.style(text, fg = "red"))


def highlightEcho(text: str) -> None:
    click.echo(click.style(text, bg = "blue"))
