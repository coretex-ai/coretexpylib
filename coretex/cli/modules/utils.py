from typing import List, Any, Optional, Callable
from functools import wraps

from py3nvml import py3nvml

import click
import inquirer


def isGPUAvailable() -> bool:
    try:
        py3nvml.nvmlInit()
        py3nvml.nvmlShutdown()
        return True
    except:
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


def onBeforeCommandExecute(fun: Callable[..., Any], excludeOptions: Optional[List[str]] = None) -> Any:
    if excludeOptions is None:
        excludeOptions = []

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for key, value in click.get_current_context().params.items():
                if key in excludeOptions and value:
                    return f(*args, **kwargs)

            fun()
            return f(*args, **kwargs)
        return wrapper
    return decorator
