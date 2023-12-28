from typing import List, Any, Optional
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


def checkIfExpired(expirationDate: datetime) -> bool:
    currentTime = datetime.utcnow().replace(tzinfo=timezone.utc)
    if currentTime >= expirationDate:
        return True
    return False


def refresh() -> None:
    print('lala')
    config = loadConfig()
    apiExpirationDate = decodeDate(config["tokenExpirationDate"])
    refreshExpirationDate = decodeDate(config["refreshTokenExpirationDate"])
    isApiExpired = checkIfExpired(apiExpirationDate)

    if not isApiExpired:
        return None

    isRefreshExpired = checkIfExpired(refreshExpirationDate)
    if not isRefreshExpired:
        refreshToken = config["refreshToken"]
        response = networkManager.authenticateWithRefreshToken(refreshToken)
    else:
        username = config["username"]
        password = config["password"]

        response = networkManager.authenticate(username, password, False)
        if response.hasFailed():
            # check for codes user/server failure
            raise RuntimeError("Something went wrong. Try configuring user again...")

    jsonResponse = response.getJson(dict)
    config["token"] = jsonResponse["token"]
    config["tokenExpirationDate"] = jsonResponse["expires_on"]
    saveConfig(config)


def validate_refresh_token(exclude_options: Optional[List[str]]) -> Any:
    if exclude_options is None:
        exclude_options = []

    def decorator(f: Any) -> Any:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for key, value in click.get_current_context().params.items():
                if key in exclude_options:
                    if value == True:
                        return f(*args, **kwargs)

            refresh()
            return f(*args, **kwargs)
        return wrapper
    return decorator
