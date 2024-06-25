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

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

import logging

from .ui import clickPrompt, errorEcho, progressEcho
from ...utils import decodeDate
from ...networking import networkManager, NetworkResponse, NetworkRequestError
from ...configuration import loadConfig, saveConfig, isUserConfigured


@dataclass
class LoginInfo:

    username: str
    password: str
    token: str
    tokenExpirationDate: str
    refreshToken: str
    refreshTokenExpirationDate: str


def hasExpired(tokenExpirationDate: Optional[str]) -> bool:
    if tokenExpirationDate is None:
        return False

    currentDate = datetime.utcnow().replace(tzinfo = timezone.utc)
    return currentDate >= decodeDate(tokenExpirationDate)


def authenticateUser(username: str, password: str) -> NetworkResponse:
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        if response.statusCode >= 500:
            raise NetworkRequestError(response, "Something went wrong, please try again later.")

        if response.statusCode >= 400:
            raise NetworkRequestError(response, "User credentials invalid.")

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

    username = clickPrompt("Email", type = str)
    password = clickPrompt("Password", type = str, hide_input = True)

    progressEcho("Authenticating...")
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        errorEcho("Failed to authenticate. Please try again...")
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


def authenticateWithTokens(config: Dict[str, Any]) -> Optional[NetworkResponse]:
    refreshToken = config.get("refreshToken")
    refreshTokenExpirationDate = config.get("refreshTokenExpirationDate")

    if refreshTokenExpirationDate is None:
        return None

    refreshTokenExpirationDate = decodeDate(refreshTokenExpirationDate)

    if refreshToken is None or hasExpired(refreshTokenExpirationDate):
        return None

    response = networkManager.authenticateWithRefreshToken(refreshToken)
    if not response.hasFailed():
        return response

    if response.statusCode >= 500:
        raise NetworkRequestError(response, "Something went wrong during authentification, please try again later.")

    return None


def initializeUserSession() -> None:
    config = loadConfig()

    if not isUserConfigured(config):
        errorEcho("User configuration not found. Please authenticate with your credentials.")
        loginInfo = authenticate()
        config = saveLoginData(loginInfo, config)
    else:
        tokenExpirationDate = config.get("tokenExpirationDate")

        if tokenExpirationDate is not None:
            tokenExpirationDate = decodeDate(tokenExpirationDate)

            if not hasExpired(tokenExpirationDate) and config.get("token") is not None:
                return

        try:
            response = authenticateWithTokens(config)

            if response is None:
                response = authenticateUser(config["username"], config["password"])

            jsonResponse = response.getJson(dict)
            config["token"] = jsonResponse["token"]
            config["tokenExpirationDate"] = jsonResponse["expires_on"]
            config["refreshToken"] = jsonResponse.get("refresh_token")
            config["refreshTokenExpirationDate"] = jsonResponse.get("refresh_expires_on")

        except NetworkRequestError as ex:
            logging.getLogger("cli").debug(ex, exc_info = ex)

            if 400 <= ex.response.statusCode < 500:
                errorEcho("Authentification failed with configured credentials. Please try entering your credentials again.")
                loginInfo = authenticate()
                config = saveLoginData(loginInfo, config)

    saveConfig(config)
