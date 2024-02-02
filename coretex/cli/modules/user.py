from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

import click

from ...utils import decodeDate
from ...networking import networkManager, NetworkResponse, NetworkRequestError
from ...configuration import loadConfig, saveConfig


@dataclass
class LoginInfo:

    username: str
    password: str
    token: str
    tokenExpirationDate: str
    refreshToken: str
    refreshTokenExpirationDate: str


def authenticateUser(username: str, password: str) -> NetworkResponse:
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        if response.statusCode >= 500:
            raise NetworkRequestError(response, "Something went wrong, please try again later.")

        if response.statusCode >= 400:
            raise NetworkRequestError(response, "User credentials invalid, please try configuring them again.")

    return response


def saveLoginData(loginInfo: LoginInfo, config: Dict[str, Any]) -> Dict[str, Any]:
    config["username"] = loginInfo.username
    config["password"] = loginInfo.password
    config["token"] = loginInfo.token
    config["tokenExpirationDate"] = loginInfo.tokenExpirationDate
    config["refreshToken"] = loginInfo.refreshToken
    config["refreshTokenExpirationDate"] = loginInfo.refreshTokenExpirationDate

    return config


def authenticate(retryCount: int = 0) -> LoginInfo:
    if retryCount >= 3:
        raise RuntimeError("Failed to authenticate. Terminating...")

    username = click.prompt("Email", type = str)
    password = click.prompt("Password", type = str, hide_input = True)

    response = networkManager.authenticate(username, password, False)
    click.echo("Authenticating...")

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


def initializeUserSession() -> None:
    config = loadConfig()

    if config.get("username") is None or config.get("password") is None:
        click.echo("User configuration not found. Please authenticate with your credentials.")
        loginInfo = authenticate()
        config = saveLoginData(loginInfo, config)
    else:
        tokenExpirationDate = decodeDate(config["tokenExpirationDate"])
        refreshTokenExpirationDate = decodeDate(config["refreshTokenExpirationDate"])

        currentDate = datetime.utcnow().replace(tzinfo = timezone.utc)

        if currentDate < tokenExpirationDate:
            return

        if currentDate < refreshTokenExpirationDate:
            refreshToken = config["refreshToken"]
            response = networkManager.authenticateWithRefreshToken(refreshToken)
            if response.hasFailed():
                if response.statusCode >= 500:
                    raise NetworkRequestError(response, "Something went wrong, please try again later.")

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
