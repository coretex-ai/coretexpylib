from pathlib import Path

import os

from tabulate import tabulate

import click

from ..configuration import loadConfig, saveConfig, isUserConfigured, isNodeConfigured
from ..networking.network_manager import NetworkManager


SERVER_URL = "dev.biomechservices.com"
NODE_PORT = 5443
CORETEX_CONFIG_DIR = Path.home() / ".config" / "coretex"


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
    while True:
        username = click.prompt("Email", type = str)
        password = click.prompt("Password", type = str, hide_input = True)
        response = NetworkManager().authenticate(username, password, False)
        if not response.hasFailed():
            click.echo("Authentification successful")
            break

        click.echo("Failed to authenticate. Try again")

    click.echo("Storage path should be the same as (if) used during --node config")
    storagePath = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)

    config["username"] = username
    config["password"] = password
    config["storagePath"] = storagePath
    config["token"] = response.getJson(dict).get("token")
    config["refreshToken"] = response.getJson(dict).get("refresh_token")

    saveConfig(config)

    click.echo("User successfuly configured")


def generateDockerScript(image: str) -> None:
    nodeSuffix = "coretex-node-dev-gpu" if image == "gpu" else "coretex-node-dev"

    dockerScriptContent = f"""#!/bin/bash
    set -e pipefail
    # coretex script

    docker-compose -f {CORETEX_CONFIG_DIR / "docker-compose.yml"} down
    docker pull {SERVER_URL}:{NODE_PORT}/{nodeSuffix}:latest
    docker-compose -f {CORETEX_CONFIG_DIR / "docker-compose.yml"} up -d
    docker ps | grep {SERVER_URL}:{NODE_PORT}/{nodeSuffix}:latest > {CORETEX_CONFIG_DIR / "container-name.log"}
    """

    dockerScript = CORETEX_CONFIG_DIR / "docker.sh"
    with open(dockerScript, "w") as dockerFile:
        dockerFile.write(dockerScriptContent)

    os.chmod(dockerScript, 0o755)


def generateDockerCompose(
    name: str,
    memory: int,
    swap: int,
    shm: int,
    organizationId: str
) -> None:

    dockerComposeContent = f"""version: "3.8"
services:
  coretex-node-service:
    image: {SERVER_URL}:{NODE_PORT}/coretex-node-dev:latest
    volumes:
      - {Path.home()}/.coretex:/root/.coretex
    environment:
      - CTX_NODE_NAME={name}
      - CTX_API_URL=https://devext.biomechservices.com:29007/
      - CTX_STORAGE_PATH=/root/.coretex
      - CTX_ORGANIZATION_ID={organizationId}
    deploy:
      replicas: 1
      update_config:
        order: start-first
    ports:
      - 21000:21000
    extra_hosts:
      - dev.biomechservices.com:192.168.135.10
    restart: always
    mem_limit: {memory}g
    memswap_limit: {swap}g
    shm_size: {shm}gb
    cap_add:
      - SYS_PTRACE
networks:
  default:
    name: coretex_node
    """

    dockerCompose = CORETEX_CONFIG_DIR / "docker-compose.yml"
    with open(dockerCompose, "w") as dockerFile:
        dockerFile.write(dockerComposeContent)


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
    organizationId = click.prompt("Organization ID", type = str)

    click.echo("Storage path should be the same as (if) used during --user config")
    storagePath = click.prompt("Storage path (press enter to use default)", Path.home() / ".coretex", type = str)

    image = click.prompt("Select an image to use for Coretex Node", type = click.Choice(["gpu", "cpu"]), show_choices = True)

    ram = click.prompt("Node RAM memory limit in GB (press enter to use default)", type = int, default = 15)
    swap = click.prompt("Node swap memory limit in GB, make sure it is larger then mem limit (press enter to use default)", type = int, default = 15)
    shm = click.prompt("Node shm limit in GB (press enter to use default)", type = int, default = 9)

    config["nodeName"] = nodeName
    config["organizationID"] = organizationId
    config["storagePath"] = storagePath
    config["image"] = image

    saveConfig(config)

    generateDockerScript(image)
    generateDockerCompose(nodeName, ram, swap, shm, organizationId)

    click.echo("[Node Setup Done] Type coretex help for additional information")
    click.echo("Important Information for Coretex Node service (command \"coretex node\"): [for using coretex node service you need to have Docker (https://www.docker.com/) installed and set up on your machine]")
    click.echo("For automatic updates, if not already, make sure \"atd\" daemon is enabled. Either with \"ps -ef | grep atd\" or \"systemctl -a | grep atd\"")
    click.echo("For additional help visit our documentation at https://docs.coretex.ai/v1/advanced/coretex-cli/troubleshooting")


@click.command()
@click.option("--user", is_flag = True, help = "Configure user settings")
@click.option("--node", is_flag = True, help = "Configure node settings")
def config(user: bool, node: bool) -> None:
    if not (user ^ node):
        raise click.UsageError("Please use either --user or --node")

    if user:
        configUser()

    if node:
        configNode()
