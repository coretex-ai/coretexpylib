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
from typing_extensions import Self

from pathlib import Path

import os
import json
import sys

from .codable import Codable, KeyDescriptor


def getEnvVar(key: str, default: str) -> str:
    if os.environ.get(key) is None:
        os.environ[key] = default

    return os.environ[key]


DEFAULT_CONFIG_PATH = Path.home().joinpath(".config", "coretex", "config.json")

DEFAULT_CONFIG = {
    # os.environ used directly here since we don't wanna
    # set those variables to any value if they don't exist
    # in the os.environ the same way we do for properties which
    # call genEnvVar
    "username": os.environ.get("CTX_USERNAME"),
    "password": os.environ.get("CTX_PASSWORD"),
    "token": None,
    "refreshToken": None,
    "serverUrl": getEnvVar("CTX_API_URL", "https://devext.biomechservices.com:29007/"),
    "storagePath": getEnvVar("CTX_STORAGE_PATH", "~/.coretex"),
}


class Configuration(Codable):

    def __init__(self) -> None:
        self.username = None
        self.password = None
        self.nodeName = None
        self.serverURL = DEFAULT_CONFIG["serverUrl"]
        self.storagePath = None
        self.token = None
        self.refreshToken = None
        self.nodeAccessToken = None
        self.tokenExpirationDate = None
        self.refreshTokenExpirationDate = None
        self.image = "cpu"
        self.nodeRam = None
        self.nodeSwap = None
        self.nodeSharedMemory = None

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["nodeName"] = KeyDescriptor("nodeName")
        descriptors["refreshToken"] = KeyDescriptor("refreshToken")
        descriptors["serverUrl"] = KeyDescriptor("serverUrl")
        descriptors["storagePath"] = KeyDescriptor("storagePath")
        descriptors["nodeAccessToken"] = KeyDescriptor("nodeAccessToken")
        descriptors["tokenExpirationDate"] = KeyDescriptor("tokenExpirationDate")
        descriptors["refreshTokenExpirationDate"] = KeyDescriptor("refreshTokenExpirationDate")
        descriptors["nodeRam"] = KeyDescriptor("nodeRam")
        descriptors["nodeSwap"] = KeyDescriptor("nodeSwap")
        descriptors["nodeSharedMemory"] = KeyDescriptor("nodeSharedMemory")

        return descriptors

    @classmethod
    def load(cls) -> Self:
        with open(DEFAULT_CONFIG_PATH, 'r') as configFile:
            configData = json.load(configFile)
            config = cls.decode(configData)
            return config

    def save(self) -> None:
        configData = self.encode() # not sure should it be done like this xD

        with open(DEFAULT_CONFIG_PATH, 'w') as configFile:
            json.dump(configData, configFile, indent = 4)


def _verifyConfiguration(config: Dict[str, Any]) -> bool:
    # Checks if all keys from default config exist in loaded one
    requiredKeys = list(DEFAULT_CONFIG.keys())
    return all(key in config.keys() for key in requiredKeys)


def _loadConfiguration(configPath: Path) -> Dict[str, Any]:
    with configPath.open("r") as configFile:
        config: Dict[str, Any] = json.load(configFile)

    if not _verifyConfiguration(config):
        raise RuntimeError(">> [Coretex] Invalid configuration")

    return config


def _syncConfigWithEnv() -> None:
    configPath = Path("~/.config/coretex/config.json").expanduser()

    # If configuration does not exist create default one
    if not configPath.exists():
        print(">> [Coretex] Configuration not found, creating default one")
        configPath.parent.mkdir(parents = True, exist_ok = True)

        with configPath.open("w") as configFile:
            json.dump(DEFAULT_CONFIG, configFile, indent = 4)

    # Load configuration and override environmet variable values
    try:
        config = _loadConfiguration(configPath)
    except BaseException as ex:
        print(">> [Coretex] Configuration is invalid")
        print(">> [Coretex] To configure user use \"coretex config --user\" command")
        print(">> [Coretex] To configure node use \"coretex config --node\" command")

        sys.exit(1)

    os.environ["CTX_API_URL"] = config["serverUrl"]
    os.environ["CTX_STORAGE_PATH"] = config["storagePath"]


def loadConfig() -> Dict[str, Any]:
    with DEFAULT_CONFIG_PATH.open("r") as configFile:
        config: Dict[str, Any] = json.load(configFile)

    if not _verifyConfiguration(config):
        raise RuntimeError(">> [Coretex] Invalid configuration")

    return config


def saveConfig(config: Configuration) -> None:
    configPath = DEFAULT_CONFIG_PATH.expanduser()
    content = config.encode()
    with configPath.open("w+") as configFile:
        json.dump(content, configFile, indent = 4)


def isUserConfigured(config: Configuration) -> bool:
    return (
        config.username is not None and
        config.password is not None and
        config.storagePath is not None
    )

def isNodeConfigured(config: Configuration) -> bool:
    return (
        config.nodeName is not None and
        config.storagePath is not None and
        config.image is not None
    )
