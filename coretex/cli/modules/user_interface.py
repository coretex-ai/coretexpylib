import click
import inquirer

from typing import Any, List, Optional


def clickPrompt(text: str, default: Any = None, type: Optional[type] = None, **kwargs: Any) -> Any:
    styled_text = click.style(text, fg = "blue")

    return click.prompt(styled_text, default = default, type = type, **kwargs)


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