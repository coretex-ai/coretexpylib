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

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import os

from . import config_defaults
from .base import BaseConfiguration, CONFIG_DIR
from ..utils import docker, isCliRuntime
from ..node import NodeMode


def getEnvVar(key: str, default: str) -> str:
    if os.environ.get(key) is None:
        return default

    return os.environ[key]


NODE_CONFIG_PATH = CONFIG_DIR / "node_config.json"
NODE_DEFAULT_CONFIG = {
    "nodeName": os.environ.get("CTX_NODE_NAME"),
    "nodeAccessToken": None,
    "storagePath": getEnvVar("CTX_STORAGE_PATH", "~/.coretex"),
    "image": "coretexai/coretex-node:latest-cpu",
    "allowGpu": False,
    "nodeRam": None,
    "nodeSharedMemory": None,
    "cpuCount": None,
    "nodeMode": None,
    "allowDocker": False,
    "nodeSecret": None,
    "initScript": None,
    "modelId": None,
}


class InvalidNodeConfiguration(Exception):
    pass


class NodeConfiguration(BaseConfiguration):

    def __init__(self) -> None:
        super().__init__(NODE_CONFIG_PATH)
        nodeSecret = self.nodeSecret
        if isinstance(nodeSecret, str) and nodeSecret != "":
            os.environ["CTX_SECRETS_KEY"] = nodeSecret

        if not isCliRuntime():
            os.environ["CTX_STORAGE_PATH"] = self.storagePath
        else:
            os.environ["CTX_STORAGE_PATH"] = f"{CONFIG_DIR}/data"

    @classmethod
    def getDefaultConfig(cls) -> Dict[str, Any]:
        return NODE_DEFAULT_CONFIG

    @property
    def nodeName(self) -> str:
        return self.getValue("nodeName", str, "CTX_NODE_NAME")

    @nodeName.setter
    def nodeName(self, value: str) -> None:
        self._raw["nodeName"] = value

    @property
    def nodeAccessToken(self) -> str:
        return self.getValue("nodeAccessToken", str)

    @nodeAccessToken.setter
    def nodeAccessToken(self, value: str) -> None:
        self._raw["nodeAccessToken"] = value

    @property
    def storagePath(self) -> str:
        return self.getValue("storagePath", str, "CTX_STORAGE_PATH")

    @storagePath.setter
    def storagePath(self, value: Optional[str]) -> None:
        self._raw["storagePath"] = value

    @property
    def image(self) -> str:
        return self.getValue("image", str)

    @image.setter
    def image(self, value: str) -> None:
        self._raw["image"] = value

    @property
    def allowGpu(self) -> bool:
        return self.getValue("allowGpu", bool)

    @allowGpu.setter
    def allowGpu(self, value: bool) -> None:
        self._raw["allowGpu"] = value

    @property
    def nodeRam(self) -> int:
        nodeRam = self.getOptValue("nodeRam", int)

        if nodeRam is None:
            nodeRam = config_defaults.DEFAULT_RAM_MEMORY

        return nodeRam

    @nodeRam.setter
    def nodeRam(self, value: int) -> None:
        self._raw["nodeRam"] = value

    @property
    def nodeSwap(self) -> int:
        nodeSwap = self.getOptValue("nodeSwap", int)

        if nodeSwap is None:
            nodeSwap = config_defaults.DEFAULT_SWAP_MEMORY

        return nodeSwap

    @nodeSwap.setter
    def nodeSwap(self, value: int) -> None:
        self._raw["nodeSwap"] = value

    @property
    def nodeSharedMemory(self) -> int:
        nodeSharedMemory = self.getOptValue("nodeSharedMemory", int)

        if nodeSharedMemory is None:
            nodeSharedMemory = config_defaults.DEFAULT_SHARED_MEMORY

        return nodeSharedMemory

    @nodeSharedMemory.setter
    def nodeSharedMemory(self, value: int) -> None:
        self._raw["nodeSharedMemory"] = value

    @property
    def cpuCount(self) -> int:
        cpuCount = self.getOptValue("cpuCount", int)

        if cpuCount is None:
            cpuCount = config_defaults.DEFAULT_CPU_COUNT

        return cpuCount

    @cpuCount.setter
    def cpuCount(self, value: int) -> None:
        self._raw["cpuCount"] = value

    @property
    def nodeMode(self) -> int:
        nodeMode = self.getOptValue("nodeMode", int)

        if nodeMode is None:
            nodeMode = NodeMode.execution

        return nodeMode

    @nodeMode.setter
    def nodeMode(self, value: int) -> None:
        self._raw["nodeMode"] = value

    @property
    def allowDocker(self) -> bool:
        return self.getValue("allowDocker", bool)

    @allowDocker.setter
    def allowDocker(self, value: bool) -> None:
        self._raw["allowDocker"] = value

    @property
    def nodeSecret(self) -> Optional[str]:
        return self.getOptValue("nodeSecret", str)

    @nodeSecret.setter
    def nodeSecret(self, value: Optional[str]) -> None:
        self._raw["nodeSecret"] = value

    @property
    def initScript(self) -> Optional[str]:
        return self.getOptValue("initScript", str)

    @initScript.setter
    def initScript(self, value: Optional[str]) -> None:
        self._raw["initScript"] = value

    @property
    def modelId(self) -> Optional[int]:
        return self.getOptValue("modelId", int)

    @modelId.setter
    def modelId(self, value: Optional[int]) -> None:
        self._raw["modelId"] = value

    @property
    def nearWalletId(self) -> Optional[str]:
        return self.getOptValue("nearWalletId", str)

    @modelId.setter
    def nearWalletId(self, value: Optional[str]) -> None:
        self._raw["nearWalletId"] = value

    @property
    def endpointInvocationPrice(self) -> Optional[float]:
        return self.getOptValue("endpointInvocationPrice", float)

    @modelId.setter
    def endpointInvocationPrice(self, value: Optional[float]) -> None:
        self._raw["endpointInvocationPrice"] = value

    def isNodeConfigured(self) -> bool:
        return (
            isinstance(self._raw.get("nodeName"), str) and
            isinstance(self._raw.get("image"), str) and
            isinstance(self._raw.get("nodeAccessToken"), str) and
            isinstance(self._raw.get("cpuCount"), int) and
            isinstance(self._raw.get("nodeRam"), int) and
            isinstance(self._raw.get("nodeSwap"), int) and
            isinstance(self._raw.get("nodeSharedMemory"), int) and
            isinstance(self._raw.get("nodeMode"), int)
        )

    def isConfigurationValid(self) -> Tuple[bool, List[str]]:
        isValid = True
        errorMessages = []
        cpuLimit, ramLimit = docker.getResourceLimits()
        swapLimit = docker.getDockerSwapLimit()

        if not isinstance(self._raw.get("nodeRam"), int):
            errorMessages.append(
                f"Invalid config \"nodeRam\" field type \"{type(self._raw.get('nodeRam'))}\". Expected: \"int\""
            )
            isValid = False

        if not isinstance(self._raw.get("cpuCount"), int):
            errorMessages.append(
                f"Invalid config \"cpuCount\" field type \"{type(self._raw.get('cpuCount'))}\". Expected: \"int\""
            )
            isValid = False

        if not isinstance(self._raw.get("nodeSwap"), int):
            errorMessages.append(
                f"Invalid config \"nodeSwap\" field type \"{type(self._raw.get('nodeSwap'))}\". Expected: \"int\""
            )
            isValid = False

        if self.cpuCount > cpuLimit:
            errorMessages.append(
                f"Configuration not valid. CPU limit in Docker Desktop ({cpuLimit}) "
                "is lower than the configured value ({self._raw.get('cpuCount')})"
            )
            isValid = False

        if ramLimit < config_defaults.MINIMUM_RAM_MEMORY:
            errorMessages.append(
                f"Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM_MEMORY}GB) "
                "is higher than your current Docker desktop RAM limit ({ramLimit}GB). "
                "Please adjust resource limitations in Docker Desktop settings to match Node requirements."
            )
            isValid = False

        if self.nodeRam > ramLimit:
            errorMessages.append(
                f"Configuration not valid. RAM limit in Docker Desktop ({ramLimit}GB) "
                "is lower than the configured value ({self._raw.get('nodeRam')}GB)"
            )
            isValid = False

        if self.nodeRam < config_defaults.MINIMUM_RAM_MEMORY:
            errorMessages.append(
                f"Configuration not valid. Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM_MEMORY}GB) "
                "is higher than the configured value ({self._raw.get('nodeRam')}GB)"
            )
            isValid = False

        if self.nodeSwap > swapLimit:
            errorMessages.append(
                f"Configuration not valid. SWAP limit in Docker Desktop ({swapLimit}GB) "
                "is lower than the configured value ({self.nodeSwap}GB)"
            )
            isValid = False

        return isValid, errorMessages


    def getInitScriptPath(self) -> Optional[Path]:
        value = self._raw.get("initScript")

        if not isinstance(value, str):
            return None

        if value == "":
            return None

        path = Path(value).expanduser().absolute()
        if not path.exists():
            return None

        return path
