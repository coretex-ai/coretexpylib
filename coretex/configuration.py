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
from pathlib import Path

import os
import json
import sys


def getEnvVar(key: str, default: str) -> str:
    if os.environ.get(key) is None:
        os.environ[key] = default

    return os.environ[key]


CONFIG_DIR = Path.home().joinpath(".config", "coretex")
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.json"


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
        configPath.parent.mkdir(parents = True, exist_ok = True)

        with configPath.open("w") as configFile:
            json.dump(DEFAULT_CONFIG, configFile, indent = 4)

    # Load configuration and override environmet variable values
    try:
        config = _loadConfiguration(configPath)
    except BaseException as ex:
        print(">> [Coretex] Configuration is invalid")
        print(">> [Coretex] To configure user use \"coretex login\" command")
        print(">> [Coretex] To configure node use \"coretex node config\" command")

        sys.exit(1)

    os.environ["CTX_API_URL"] = config["serverUrl"]
    os.environ["CTX_STORAGE_PATH"] = config["storagePath"]


def loadConfig() -> Dict[str, Any]:
    with DEFAULT_CONFIG_PATH.open("r") as configFile:
        config: Dict[str, Any] = json.load(configFile)

    if not _verifyConfiguration(config):
        raise RuntimeError(">> [Coretex] Invalid configuration")

    return config


def saveConfig(config: Dict[str, Any]) -> None:
    configPath = DEFAULT_CONFIG_PATH.expanduser()
    with configPath.open("w+") as configFile:
        json.dump(config, configFile, indent = 4)


def isUserConfigured(config: Dict[str, Any]) -> bool:
    return (
        config.get("username") is not None and
        config.get("password") is not None and
        config.get("storagePath") is not None
    )

def isNodeConfigured(config: Dict[str, Any]) -> bool:
    return (
        config.get("nodeName") is not None and
        config.get("storagePath") is not None and
        config.get("image") is not None and
        config.get("serverUrl") is not None and
        config.get("nodeAccessToken") is not None and
        config.get("nodeRam") is not None and
        config.get("nodeSwap") is not None and
        config.get("nodeSharedMemory") is not None
    )
