from pathlib import Path

import os

from tabulate import tabulate

import click

from .utils import arrowPrompt
from ..configuration import loadConfig, saveConfig, isUserConfigured, isNodeConfigured, getNodeAccessToken
from ..statistics import getAvailableRamMemory
from ..networking import networkManager


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
    for i in range(3):
        username = click.prompt("Email", type = str)
        password = click.prompt("Password", type = str, hide_input = True)
        response = networkManager.authenticate(username, password, False)
        if not response.hasFailed():
            click.echo("Authentification successful")
            break

        click.echo("Failed to authenticate. Try again")

    click.echo("Storage path should be the same as (if) used during --node config")
    storagePath = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)

    jsonResponse = response.getJson(dict)

    config["username"] = username
    config["password"] = password
    config["storagePath"] = storagePath
    config["token"] = jsonResponse.get("token")
    config["refreshToken"] = jsonResponse.get("refresh_token")

    saveConfig(config)

    click.echo("User successfuly configured")


def configNode() -> None:
    config = loadConfig()
    if not isUserConfigured(config):
        click.echo("User not configured. Run \'coretex config --user\'", err = True)
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
    nodeAccessToken = getNodeAccessToken(nodeName)

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
    click.echo("Important Information for Coretex Node service (command \"coretex node\"): [for using coretex node service you need to have Docker (https://www.docker.com/) installed and set up on your machine]")
    click.echo("For automatic updates, if not already, make sure \"atd\" daemon is enabled. Either with \"ps -ef | grep atd\" or \"systemctl -a | grep atd\"")
    click.echo("For additional help visit our documentation at https://docs.coretex.ai/v1/advanced/coretex-cli/troubleshooting")


@click.command()
@click.option("--user", is_flag = True, help = "Configure user settings")
@click.option("--node", is_flag = True, help = "Configure node settings")
def config(user: bool, node: bool) -> None:
    if not user and not node:
        raise click.UsageError("Please use either --user or --node")

    if user is not None:
        configUser()

    if node is not None:
        configNode()
