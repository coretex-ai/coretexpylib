from dataclasses import dataclass
from pathlib import Path

import click

from ...networking import networkManager
from ...configuration import loadConfig, saveConfig, isUserConfigured


@dataclass
class LoginInfo:

    username: str
    password: str
    token: str
    tokenExpirationDate: str
    refreshToken: str
    refreshTokenExpirationDate: str


def authenticate(retryCount: int = 0) -> LoginInfo:
    if retryCount >= 3:
        raise Exception("Failed to authenticate. Terminating...")

    username = click.prompt("Email", type = str)
    password = click.prompt("Password", type = str, hide_input = True)

    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        click.echo("Failed to authenticate. Please try again...")
        return authenticate(retryCount + 1)

    jsonResponse = response.getJson(dict)

    return LoginInfo(
        username,
        password,
        jsonResponse["token"],
        jsonResponse["expires_on"],
        jsonResponse["refresh_token"],
        jsonResponse["refresh_expires_on"]
    )


@click.command()
def login() -> None:
    config = loadConfig()
    if isUserConfigured(config):
        if not click.prompt(
            f"User already logged in with username {config['username']}. Would you like to log in with different user (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    loginInfo = authenticate()

    storagePath = str(Path.home() / ".coretex")

    config["username"] = loginInfo.username
    config["password"] = loginInfo.password
    config["token"] = loginInfo.token
    config["refreshToken"] = loginInfo.refreshToken
    config["storagePath"] = storagePath
    config["tokenExpirationDate"] = loginInfo.tokenExpirationDate
    config["refreshTokenExpirationDate"] = loginInfo.refreshTokenExpirationDate

    saveConfig(config)

    click.echo(f"User {config['username']} successfully logged in.")
