from typing import List, Any, Optional, Callable
from datetime import datetime, timezone
from functools import wraps

import click
import inquirer

from py3nvml import py3nvml

from ..utils import decodeDate
from ..configuration import loadConfig, saveConfig
from ..networking import networkManager


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


def authenticateUser(username: str, password: str) -> None:
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        if response.statusCode >= 500:
            raise RuntimeError("Something went wrong, please try again later.")

        if response.statusCode >= 400:
            raise RuntimeError("User credentials invalid, please try configuring them again.")


def initializeUserSession() -> None:
    config = loadConfig()
    tokenExpirationDate = decodeDate(config["tokenExpirationDate"])
    refreshTokenExpirationDate = decodeDate(config["refreshTokenExpirationDate"])

    if datetime.utcnow().replace(tzinfo = timezone.utc) < tokenExpirationDate:
        return

    if datetime.utcnow().replace(tzinfo = timezone.utc) < refreshTokenExpirationDate:
        refreshToken = config["refreshToken"]
        response = networkManager.authenticateWithRefreshToken(refreshToken)
        if response.hasFailed():
            if response.statusCode >= 500:
                raise RuntimeError("Something went wrong, please try again later.")

            if response.statusCode >= 400:
                authenticateUser(config["username"], config["password"])
    else:
        authenticateUser(config["username"], config["password"])

    jsonResponse = response.getJson(dict)
    config["token"] = jsonResponse["token"]
    config["tokenExpirationDate"] = jsonResponse["expires_on"]
    saveConfig(config)


def validate(excludeOptions: Optional[List[str]] = None) -> Any:
    if excludeOptions is None:
        excludeOptions = []

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for key, value in click.get_current_context().params.items():
                if key in excludeOptions:
                    if value:
                        return f(*args, **kwargs)

            initializeUserSession()
            return f(*args, **kwargs)
        return wrapper
    return decorator
