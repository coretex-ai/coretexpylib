#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Dict, Any
from datetime import datetime, timezone

from .ui import clickPrompt, errorEcho, progressEcho
from ...utils import decodeDate
from ...networking import networkManager, NetworkRequestError
from ...configuration import loadConfig, saveConfig, isUserConfigured


def configUser(config: Dict[str, Any], retryCount: int = 0) -> None:
    if retryCount >= 3:
        raise RuntimeError("Failed to authenticate. Terminating...")

    username = clickPrompt("Email", type = str)
    password = clickPrompt("Password", type = str, hide_input = True)

    progressEcho("Authenticating...")
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        errorEcho("Failed to authenticate. Please try again...")
        return configUser(config, retryCount + 1)

    jsonResponse = response.getJson(dict)
    config["username"] = username
    config["password"] = password
    config["token"] = jsonResponse["token"]
    config["tokenExpirationDate"] = jsonResponse["expires_on"]
    config["refreshToken"] = jsonResponse.get("refresh_token")
    config["refreshTokenExpirationDate"] = jsonResponse.get("refresh_expires_on")


def authenticateUser(config: Dict[str, Any]) -> None:
    response = networkManager.authenticate(config["username"], config["password"])

    if response.statusCode >= 500:
        raise NetworkRequestError(response, "Something went wrong, please try again later.")
    elif response.statusCode >= 400:
        configUser(config)
    else:
        jsonResponse = response.getJson(dict)
        config["token"] = jsonResponse["token"]
        config["tokenExpirationDate"] = jsonResponse["expires_on"]
        config["refreshToken"] = jsonResponse.get("refresh_token")
        config["refreshTokenExpirationDate"] = jsonResponse.get("refresh_expires_on")


def getRefreshToken(config: Dict[str, Any]) -> str:
    refreshToken = config.get("refreshToken")

    if not isinstance(refreshToken, str):
        raise TypeError(f"Expected \"str\" received \"{type(refreshToken)}\"")

    return refreshToken


def authenticateWithRefreshToken(config: Dict[str, Any]) -> None:
    response = networkManager.authenticateWithRefreshToken(getRefreshToken(config))

    if response.statusCode >= 500:
        raise NetworkRequestError(response, "Something went wrong, please try again later.")
    elif response.statusCode >= 400:
        authenticateUser(config)
    else:
        jsonResponse = response.getJson(dict)
        config["token"] = jsonResponse["token"]
        config["tokenExpirationDate"] = jsonResponse["expires_on"]


def isTokenValid(config: Dict[str, Any], tokenName: str) -> bool:
    tokenValue = config.get(tokenName)
    if not isinstance(tokenValue, str) or len(tokenValue) == 0:
        return False

    tokenExpirationDate = config.get(f"{tokenName}ExpirationDate")
    if not isinstance(tokenExpirationDate, str) or len(tokenExpirationDate) == 0:
        return False

    try:
        return datetime.now(timezone.utc) > decodeDate(tokenExpirationDate)
    except ValueError:
        return False


def initializeUserSession() -> None:
    config = loadConfig()

    if not isUserConfigured(config):
        errorEcho("User configuration not found. Please authenticate with your credentials.")
        configUser(config)
    elif not isTokenValid(config, "token") and isTokenValid(config, "refreshToken"):
        authenticateWithRefreshToken(config)
    else:
        authenticateUser(config)

    saveConfig(config)
