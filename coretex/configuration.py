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
from pathlib import Path

import os
import json
import sys


def isCliRuntime() -> bool:
    executablePath = sys.argv[0]
    return (
        executablePath.endswith("/bin/coretex") and
        os.access(executablePath, os.X_OK)
    )


def getEnvVar(key: str, default: str) -> str:
    if os.environ.get(key) is None:
        return default

    return os.environ[key]


CONFIG_DIR = Path.home().joinpath(".config", "coretex")
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.json"


DEFAULT_CONFIG: Dict[str, Any] = {
    # os.environ used directly here since we don't wanna
    # set those variables to any value if they don't exist
    # in the os.environ the same way we do for properties which
    # call genEnvVar
    "username": os.environ.get("CTX_USERNAME"),
    "password": os.environ.get("CTX_PASSWORD"),
    "token": None,
    "refreshToken": None,
    "serverUrl": getEnvVar("CTX_API_URL", "https://api.coretex.ai/"),
    "storagePath": getEnvVar("CTX_STORAGE_PATH", "~/.coretex")
}


def loadConfig() -> Dict[str, Any]:
    with DEFAULT_CONFIG_PATH.open("r") as configFile:
        try:
            config: Dict[str, Any] = json.load(configFile)
        except json.JSONDecodeError:
            config = {}

    for key, value in DEFAULT_CONFIG.items():
        if not key in config:
            config[key] = value

    return config


def _syncConfigWithEnv() -> None:
    # If configuration does not exist create default one
    if not DEFAULT_CONFIG_PATH.exists():
        DEFAULT_CONFIG_PATH.parent.mkdir(parents = True, exist_ok = True)
        config = DEFAULT_CONFIG.copy()
    else:
        config = loadConfig()

    saveConfig(config)

    if not "CTX_API_URL" in os.environ:
        os.environ["CTX_API_URL"] = config["serverUrl"]

    secretsKey = config.get("secretsKey")
    if isinstance(secretsKey, str) and secretsKey != "":
        os.environ["CTX_SECRETS_KEY"] = secretsKey

    if not isCliRuntime():
        os.environ["CTX_STORAGE_PATH"] = config["storagePath"]
    else:
        os.environ["CTX_STORAGE_PATH"] = str(CONFIG_DIR)


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
        config.get("nodeSharedMemory") is not None and
        config.get("nodeMode") is not None
    )


def getInitScript(config: Dict[str, Any]) -> Optional[Path]:
    value = config.get("initScript")

    if not isinstance(value, str):
        return None

    if value == "":
        return None

    path = Path(value).expanduser().absolute()
    if not path.exists():
        return None

    return path
