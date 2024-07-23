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

from . import ui
from ...networking import networkManager, NetworkRequestError
from ...configuration import UserConfiguration


def configUser(userConfig: UserConfiguration, retryCount: int = 0) -> None:
    if retryCount >= 3:
        raise RuntimeError("Failed to authenticate. Terminating...")

    username = ui.clickPrompt("Email", type = str)
    password = ui.clickPrompt("Password", type = str, hide_input = True)

    ui.progressEcho("Authenticating...")
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        ui.errorEcho("Failed to authenticate. Please try again...")
        return configUser(userConfig, retryCount + 1)

    jsonResponse = response.getJson(dict)
    userConfig.username = username
    userConfig.password = password
    userConfig.token = jsonResponse["token"]
    userConfig.tokenExpirationDate = jsonResponse["expires_on"]
    userConfig.refreshToken = jsonResponse.get("refresh_token")
    userConfig.refreshTokenExpirationDate = jsonResponse.get("refresh_expires_on")


def authenticateUser(userConfig: UserConfiguration) -> None:
    response = networkManager.authenticate(userConfig.username, userConfig.password)

    if response.statusCode >= 500:
        raise NetworkRequestError(response, "Something went wrong, please try again later.")
    elif response.statusCode >= 400:
        configUser(userConfig)
    else:
        jsonResponse = response.getJson(dict)
        userConfig.token = jsonResponse["token"]
        userConfig.tokenExpirationDate = jsonResponse["expires_on"]
        userConfig.refreshToken = jsonResponse.get("refresh_token")
        userConfig.refreshTokenExpirationDate = jsonResponse.get("refresh_expires_on")


def authenticateWithRefreshToken(userConfig: UserConfiguration) -> None:
    if not isinstance(userConfig.refreshToken, str):
        raise TypeError(f"Expected \"str\" received \"{type(userConfig.refreshToken)}\"")

    response = networkManager.authenticateWithRefreshToken(userConfig.refreshToken)

    if response.statusCode >= 500:
        raise NetworkRequestError(response, "Something went wrong, please try again later.")
    elif response.statusCode >= 400:
        authenticateUser(userConfig)
    else:
        jsonResponse = response.getJson(dict)
        userConfig.token = jsonResponse["token"]
        userConfig.token = jsonResponse["expires_on"]


def initializeUserSession() -> None:
    userConfig = UserConfiguration()

    if not userConfig.isUserConfigured():
        ui.errorEcho("User configuration not found. Please authenticate with your credentials.")
        configUser(userConfig)
    elif not userConfig.isTokenValid("token") and userConfig.isTokenValid("refreshToken"):
        authenticateWithRefreshToken(userConfig)
    else:
        authenticateUser(userConfig)

    userConfig.save()
