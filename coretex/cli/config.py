from typing import Tuple
from pathlib import Path

from tabulate import tabulate
from datetime import datetime, timedelta

import click

from .utils import arrowPrompt, checkIfGPUExists
from ..utils import decodeDate
from ..networking import networkManager
from ..statistics import getAvailableRamMemory
from ..configuration import loadConfig, saveConfig, isUserConfigured, isNodeConfigured


API_EXPIRE_SEC = 3600
REFRESH_EXPIRE_SEC = 86400


def checkIfExpired(expirationDate: datetime, expirationTimeSec: int) -> bool:
    expirationTime = expirationDate + timedelta(seconds = expirationTimeSec)
    currentTime = datetime.utcnow().replace(tzinfo = expirationDate.tzinfo)
    if currentTime >= expirationTime:
        return True

    return False


def refresh() -> None:
    print('refresh')
    config = loadConfig()
    apiExpirationDate = decodeDate(config["apiTokenExpireDate"])
    refreshExpirationDate = decodeDate(config["refreshTokenExpireDate"])
    isApiExpired = checkIfExpired(apiExpirationDate, 10)

    if isApiExpired:
        isRefreshExpired = checkIfExpired(refreshExpirationDate, REFRESH_EXPIRE_SEC)

        if isRefreshExpired:
            username = config["username"]
            password = config["password"]

            response = networkManager.authenticate(username, password, False)
            if response.hasFailed():
                raise RuntimeError("Something went wrong. Try configuring user again...")
        else:
            refreshToken = config["refreshToken"]
            response = networkManager.authenticateWithRefreshToken(refreshToken)

        jsonResponse = response.getJson(dict)
        config["token"] = jsonResponse["token"]
        config["expiresOn"] = jsonResponse["expires_on"]
        saveConfig(config)


def authenticate(retryCount: int = 0, refresh: bool = False) -> Tuple[str, str, str, str, str, str]:
    if retryCount >= 3:
        raise Exception("Failed to authenticate. Terminating...")

    username = click.prompt("Email", type = str)
    password = click.prompt("Password", type = str, hide_input = True)

    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        click.echo("Failed to authenticate. Please try again...")
        return authenticate(retryCount + 1)

    jsonResponse = response.getJson(dict)

    return (
        username,
        password,
        jsonResponse["token"],
        jsonResponse["expires_on"],
        jsonResponse["refresh_token"],
        jsonResponse['refresh_expires_on']
    )


def registerNode(name: str) -> str:
    params = {
        "machine_name": name
    }
    response = networkManager.post("service", params)

    if response.hasFailed():
        raise Exception("Failed to configure node. Please try again...")

    accessToken = response.getJson(dict).get("access_token")

    if not isinstance(accessToken, str):
        raise TypeError("Something went wrong. Please try again...")

    return accessToken

def configUser() -> None:
    config = loadConfig()
    if isUserConfigured(config):
        headers = ["username", "server", "storage path"]

        click.echo(click.style("Current Configuration:", fg = "blue"))
        click.echo(tabulate([[
            config.get("username"),
            config.get("serverUrl"),
            config.get("storagePath")
        ]], headers = headers))

        if not click.prompt(
            "User configuration already exists. Would you like to update (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    click.echo("Configuring user...")
    username, password, token, tokenExpireDate, refreshToken, refreshTokenExpireDate = authenticate()

    click.echo("Storage path should be the same as (if) used during --node config")
    storagePath = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)

    config["token"] = token
    config["username"] = username
    config["password"] = password
    config["storagePath"] = storagePath
    config["refreshToken"] = refreshToken
    config["apiTokenExpireDate"] = tokenExpireDate
    config["refreshTokenExpireDate"] = refreshTokenExpireDate

    saveConfig(config)

    click.echo("User successfuly configured")


def configNode() -> None:
    config = loadConfig()
    if not isUserConfigured(config):
        click.echo("User not configured. Run \"coretex config --user\"", err = True)
        return

    if isNodeConfigured(config):
        headers = ["node name", "server", "storage path", "node image"]

        click.echo(click.style("Current Configuration:", fg = "blue"))
        click.echo(tabulate([[
            config.get("nodeName"),
            config.get("serverUrl"),
            config.get("storagePath"),
            config.get("image")
        ]], headers = headers))

        if not click.prompt(
            "Node configuration already exists. Would you like to update (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    click.echo("[Setting up coretex environment]")
    click.echo("[Node Configuration]")

    nodeName = click.prompt("Node name", type = str)
    nodeAccessToken = registerNode(nodeName)

    click.echo("Storage path should be the same as (if) used during --user config")
    storagePath = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)

    gpuExists = checkIfGPUExists()
    if gpuExists:
        image = arrowPrompt(["gpu", "cpu"])
    else:
        image = "cpu"

    ram = click.prompt("Node RAM memory limit in GB (press enter to use default)", type = int, default = getAvailableRamMemory())
    swap = click.prompt("Node swap memory limit in GB, make sure it is larger then mem limit (press enter to use default)", type = int, default = getAvailableRamMemory() * 2)
    sharedMemory = click.prompt("Node POSIX shared memory limit in GB (press enter to use default)", type = int, default = 2)

    config["nodeImage"] = image
    config["nodeName"] = nodeName
    config["nodeRam"] = f"{ram}gb"
    config["nodeSwap"] = f"{swap}gb"
    config["storagePath"] = storagePath
    config["nodeAccessToken"] = nodeAccessToken
    config["nodeSharedMemory"] = f"{sharedMemory}gb"

    saveConfig(config)

    click.echo("[Node Setup Done] Type \"coretex --help\" for additional information")
    click.echo("For additional help visit our documentation at https://docs.coretex.ai/v1/advanced/coretex-cli/troubleshooting")


@click.command()
@click.option("--user", is_flag = True, help = "Configure user settings")
@click.option("--node", is_flag = True, help = "Configure node settings")
def config(user: bool, node: bool) -> None:
    if not user and not node:
        raise click.UsageError("Please use either --user or --node")

    if user:
        configUser()

    if node:
        configNode()
