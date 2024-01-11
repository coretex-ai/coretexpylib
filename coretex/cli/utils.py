from typing import List, Any, Optional, Callable
from datetime import datetime, timezone

import click
import inquirer

from functools import wraps

from ..utils import decodeDate
from ..configuration import loadConfig, saveConfig
from ..networking import networkManager


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


def refresh() -> None:
    print('refresh sda')
    config = loadConfig()
    tokenExpirationDate = decodeDate(config["tokenExpirationDate"])
    refreshTokenExpirationDate = decodeDate(config["refreshTokenExpirationDate"])

    if datetime.utcnow().replace(tzinfo = timezone.utc) < tokenExpirationDate:
        return None

    if datetime.utcnow().replace(tzinfo = timezone.utc) < refreshTokenExpirationDate:
        refreshToken = config["refreshToken"]
        response = networkManager.authenticateWithRefreshToken(refreshToken)
        if response.hasFailed():
            if str(response.statusCode)[0] == 5:
                raise RuntimeError("Something went wrong on server side. Please try again later.")

            if str(response.statusCode)[0] == 4:
                raise RuntimeError("Something went wrong. Please try again...")
    else:
        username = config["username"]
        password = config["password"]

        response = networkManager.authenticate(username, password, False)
        if response.hasFailed():
            if str(response.statusCode)[0] == 5:
                raise RuntimeError("Something went wrong on server side. Please try again later.")

            if str(response.statusCode)[0] == 4:
                raise RuntimeError("Something went wrong. Please try again...")

    jsonResponse = response.getJson(dict)
    config["token"] = jsonResponse["token"]
    config["tokenExpirationDate"] = jsonResponse["expires_on"]
    saveConfig(config)


def validate(excludeOptions: Optional[List[str]]) -> Any:
    if excludeOptions is None:
        excludeOptions = []

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for key, value in click.get_current_context().params.items():
                if key in excludeOptions:
                    if value:
                        return f(*args, **kwargs)

            refresh()
            return f(*args, **kwargs)
        return wrapper
    return decorator
