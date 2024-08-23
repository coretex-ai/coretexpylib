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

import requests

from . import ui
from ...networking import networkManager, NetworkRequestError, baseUrl
from ...configuration import UserConfiguration, InvalidConfiguration, ConfigurationNotFound


def validateServerUrl(serverUrl: str) -> bool:
    try:
        endpoint = baseUrl(serverUrl) + "/info.json"
        response = requests.get(endpoint, timeout = 5)
        return response.ok
    except BaseException as ex:
        return False


def configureServerUrl() -> str:
    availableChoices = ["Official Coretex Server URL", "Custom Server URL"]
    selectedChoice = ui.arrowPrompt(availableChoices, "Please select server url that you want to use (use arrow keys to select an option):")

    if not "Official" in selectedChoice:
        serverUrl: str = ui.clickPrompt("Enter server url that you wish to use", type = str)

        if not validateServerUrl(serverUrl):
            ui.warningEcho("You've entered invalid server url. Please try again.")
            serverUrl = configureServerUrl()

        return serverUrl

    return "https://api.coretex.ai/"

def configUser(retryCount: int = 0) -> UserConfiguration:
    if retryCount >= 3:
        raise RuntimeError("Failed to authenticate. Terminating...")

    userConfig = UserConfiguration({})  # create new empty user config
    userConfig.serverUrl = configureServerUrl()
    username = ui.clickPrompt("Email", type = str)
    password = ui.clickPrompt("Password", type = str, hide_input = True)

    ui.progressEcho("Authenticating...")
    response = networkManager.authenticate(username, password, False)

    if response.hasFailed():
        ui.errorEcho("Failed to authenticate. Please try again...")
        return configUser(retryCount + 1)

    jsonResponse = response.getJson(dict)
    userConfig.username = username
    userConfig.password = password
    userConfig.token = jsonResponse["token"]
    userConfig.tokenExpirationDate = jsonResponse["expires_on"]
    userConfig.refreshToken = jsonResponse.get("refresh_token")
    userConfig.refreshTokenExpirationDate = jsonResponse.get("refresh_expires_on")

    return userConfig


def authenticateUser(userConfig: UserConfiguration) -> None:
    response = networkManager.authenticate(userConfig.username, userConfig.password)

    if response.statusCode >= 500:
        raise NetworkRequestError(response, "Something went wrong, please try again later.")
    elif response.statusCode >= 400:
        ui.errorEcho(f"Failed to authenticate with stored credentials (Server URL: {userConfig.serverUrl}).")
        if not ui.clickPrompt("Would you like to reconfigure the user? (Y/n)", type = bool, default = True, show_default = False):
            raise RuntimeError

        userConfig.update(configUser())
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
    try:
        userConfig = UserConfiguration.load()
        if userConfig.isTokenValid("token"):
            return

        if not userConfig.isTokenValid("token") and userConfig.isTokenValid("refreshToken"):
            authenticateWithRefreshToken(userConfig)
        else:
            authenticateUser(userConfig)
    except ConfigurationNotFound:
        ui.errorEcho("User configuration not found.")
        if not ui.clickPrompt("Would you like to configure the user? (Y/n)", type = bool, default = True, show_default = False):
            raise

        userConfig = configUser()
    except InvalidConfiguration as ex:
        ui.errorEcho("Invalid user configuration found.")
        for error in ex.errors:
            ui.errorEcho(f"{error}")

        if not ui.clickPrompt("Would you like to reconfigure the user? (Y/n)", type = bool, default = True, show_default = False):
            raise

        userConfig = configUser()

    userConfig.save()
