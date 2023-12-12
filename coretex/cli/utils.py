from typing import List, Any

import inquirer


def arrowPrompt(choices: List[Any]) -> Any:
    answers = inquirer.prompt([
        inquirer.List(
            "option",
            message = "Use arrow keys to select an option",
            choices = choices,
            carousel = True,
        )
    ])

    return answers['option']
