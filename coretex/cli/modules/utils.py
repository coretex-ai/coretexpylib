from typing import List, Any, Optional, Callable
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from py3nvml import py3nvml

import click
import inquirer

from ..commands.login import authenticate
from ...utils import decodeDate
from ...configuration import loadConfig, saveConfig, isNodeConfigured
from ...networking import networkManager, NetworkResponse

from . import node as node_module


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


def authenticateUser(username: str, password: str) -> NetworkResponse:
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        if response.statusCode >= 500:
            raise RuntimeError("Something went wrong, please try again later.")

        if response.statusCode >= 400:
            raise RuntimeError("User credentials invalid, please try configuring them again.")

    return response


def initializeUserSession() -> None:
    config = loadConfig()

    if config.get("username") is None or config.get("password") is None:
        loginInfo = authenticate()
        config["username"] = loginInfo.username
        config["password"] = loginInfo.password
        config["token"] = loginInfo.token
        config["tokenExpirationDate"] = loginInfo.tokenExpirationDate
        config["refreshToken"] = loginInfo.refreshToken
        config["refreshTokenExpirationDate"] = loginInfo.refreshTokenExpirationDate
        saveConfig(config)

    else:
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
                    response = authenticateUser(config["username"], config["password"])

        else:
            response = authenticateUser(config["username"], config["password"])

        jsonResponse = response.getJson(dict)
        config["token"] = jsonResponse["token"]
        config["tokenExpirationDate"] = jsonResponse["expires_on"]
        config["refreshToken"] = jsonResponse.get("refresh_token", config["refreshToken"])
        config["refreshTokenExpirationDate"] = jsonResponse.get("refresh_expires_on", config["refreshTokenExpirationDate"])
        saveConfig(config)


def initializeNodeConfiguration() -> None:
    config = loadConfig()
    if not isNodeConfigured(config):
        click.echo("Node configuration not found.")
        click.echo("[Node Configuration]")

        config["storagePath"] = str(Path.home() / ".coretex")
        config["nodeName"] = click.prompt("Node name", type = str)
        config["nodeAccessToken"] = node_module.registerNode(config["nodeName"])

        if isGPUAvailable():
            isGPU = click.prompt("Would you like to allow access to GPU on your node (Y/n)?", type = bool, default = True)
            config["image"] = "gpu" if isGPU else "cpu"
        else:
            config["image"] = "cpu"

        config["nodeRam"] = node_module.DEFAULT_RAM_MEMORY
        config["nodeSwap"] = node_module.DEFAULT_SWAP_MEMORY
        config["nodeSharedMemory"] = node_module.DEFAULT_SHARED_MEMORY

        saveConfig(config)


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
