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

from pathlib import Path

import os
import json
import logging

from .user import UserConfiguration
from .node import NodeConfiguration
from .base import CONFIG_DIR, DEFAULT_VENV_PATH, InvalidConfiguration, ConfigurationNotFound
from ..utils import isCliRuntime


def configMigration(configPath: Path) -> None:
    with configPath.open("r") as file:
        oldConfig = json.load(file)
        logging.warning(f"[Coretex] >> WARNING: Old configuration:\n{oldConfig}")

    userRaw = {
        "username": oldConfig.get("username"),
        "password": oldConfig.get("password"),
        "token": oldConfig.get("token"),
        "refreshToken": oldConfig.get("refreshToken"),
        "tokenExpirationDate": oldConfig.get("tokenExpirationDate"),
        "refreshTokenExpirationDate": oldConfig.get("refreshTokenExpirationDate"),
        "serverUrl": oldConfig.get("serverUrl"),
        "projectId": oldConfig.get("projectId"),
    }

    nodeRaw = {
        "nodeName": oldConfig.get("nodeName"),
        "nodeAccessToken": oldConfig.get("nodeAccessToken"),
        "storagePath": oldConfig.get("storagePath"),
        "image": oldConfig.get("image"),
        "allowGpu": oldConfig.get("allowGpu"),
        "nodeRam": oldConfig.get("nodeRam"),
        "nodeSharedMemory": oldConfig.get("nodeSharedMemory"),
        "nodeSwap": oldConfig.get("nodeSwap"),
        "cpuCount": oldConfig.get("cpuCount"),
        "nodeMode": oldConfig.get("nodeMode"),
        "allowDocker": oldConfig.get("allowDocker"),
        "nodeSecret": oldConfig.get("nodeSecret"),
        "initScript": oldConfig.get("initScript"),
        "modelId": oldConfig.get("modelId"),
        "nodeId": oldConfig.get("nodeId")
    }

    userConfig = UserConfiguration(userRaw)
    nodeConfig = NodeConfiguration(nodeRaw)
    userConfig.save()
    nodeConfig.save()
    configPath.unlink()


def _syncConfigWithEnv() -> None:
    # If configuration doesn't exist default one will be created
    # Initialization of User and Node Configuration classes will do
    # the necessary sync between config properties and corresponding
    # environment variables (e.g. storagePath -> CTX_STORAGE_PATH)

    # old configuration exists, fill out new config files with old configuration
    oldConfigPath = CONFIG_DIR / "config.json"
    if oldConfigPath.exists():
        logging.warning(
            f"[Coretex] >> WARNING: Old configuration found at path: {oldConfigPath}. Migrating to new configuration."
            f"\nFields with invalid values might be overrided in this process."
        )
        configMigration(oldConfigPath)

    try:
        userConfig = UserConfiguration.load()
        if not "CTX_API_URL" in os.environ:
            os.environ["CTX_API_URL"] = userConfig.serverUrl
    except (ConfigurationNotFound, InvalidConfiguration) as ex:
        if not isCliRuntime():
            logging.error(f">> [Coretex] Error loading configuration. Reason: {ex}")
            logging.info("\tIf this message came from Coretex Node you can safely ignore it.")

    try:
        nodeConfig = NodeConfiguration.load()

        if isinstance(nodeConfig.nodeSecret, str) and nodeConfig.nodeSecret != "":
            os.environ["CTX_SECRETS_KEY"] = nodeConfig.nodeSecret

        if not isCliRuntime():
            os.environ["CTX_STORAGE_PATH"] = nodeConfig.storagePath
        else:
            os.environ["CTX_STORAGE_PATH"] = f"{CONFIG_DIR}/data"
    except (ConfigurationNotFound, InvalidConfiguration) as ex:
        if not isCliRuntime():
            logging.error(f">> [Coretex] Error loading configuration. Reason: {ex}")
            logging.info("\tIf this message came from Coretex Node you can safely ignore it.")
