from typing import List, Any

import inquirer


def arrowPrompt(choices: List[Any]) -> Any:
    questions = [
        inquirer.List('option',
                      message = "Use arrow keys to select an option:",
                      choices = choices,
                      carousel = True,
                      ),
    ]

    answers = inquirer.prompt(questions)

    return answers['option']