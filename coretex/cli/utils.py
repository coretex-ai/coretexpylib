from typing import List, Any

import click
import inquirer


def isGPUAvailable() -> bool:
    try:
        from py3nvml import py3nvml

        py3nvml.nvmlInit()
        py3nvml.nvmlShutdown()
        return True
    except:
        click.echo("This machine cannot utilize gpu image since it doesn't posses GPU.\bCPU image will be selected automatically")
        return False


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
