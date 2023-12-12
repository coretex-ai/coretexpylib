from typing import Optional, Tuple
from pathlib import Path

from tabulate import tabulate

import click

from .utils import arrowPrompt
from ..networking import networkManager
from ..statistics import getAvailableRamMemory
from ..configuration import loadConfig, saveConfig, isUserConfigured, isNodeConfigured


def authenticate(retryCount: int = 0) -> Tuple[str, str, str, str]:
    if retryCount >= 3:
        raise Exception("Failed to authenticate. Terminating...")

    username = click.prompt("Email", type = str)
    password = click.prompt("Password", type = str, hide_input = True)

    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        click.echo("Failed to authenticate. Please try again...")
        return authenticate(retryCount + 1)

    jsonResponse = response.getJson(dict)

    return username, password, jsonResponse["token"], jsonResponse["refresh_token"]


def registerNode(name: str) -> Optional[str]:
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
    username, password, token, refreshToken = authenticate()

    click.echo("Storage path should be the same as (if) used during --node config")
    storagePath = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)

    config["username"] = username
    config["password"] = password
    config["storagePath"] = storagePath
    config["token"] = token
    config["refreshToken"] = refreshToken

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

    nodeName = click.prompt("Machine name", type = str)
    nodeAccessToken = registerNode(nodeName)

    if nodeAccessToken is None:
        return

    click.echo("Storage path should be the same as (if) used during --user config")
    storagePath = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)

    image = arrowPrompt(["gpu", "cpu"])

    ram = click.prompt("Node RAM memory limit in GB (press enter to use default)", type = int, default = getAvailableRamMemory())
    swap = click.prompt("Node swap memory limit in GB, make sure it is larger then mem limit (press enter to use default)", type = int, default = getAvailableRamMemory() * 2)
    sharedMemory = click.prompt("Node POSIX shared memory limit in GB (press enter to use default)", type = int, default = 2)

    config["nodeName"] = nodeName
    config["storagePath"] = storagePath
    config["image"] = image
    config["nodeAccessToken"] = nodeAccessToken

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
