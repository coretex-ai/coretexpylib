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
from ..utils import docker
from ..node import NodeMode
from ..networking import networkManager, NetworkRequestError


def getEnvVar(key: str, default: str) -> str:
    if os.environ.get(key) is None:
        return default

    return os.environ[key]


class DockerConfigurationException(Exception):
    pass


class NodeConfiguration(BaseConfiguration):

    def __init__(self, raw: Dict[str, Any]) -> None:
        super().__init__(raw)

    @classmethod
    def getConfigPath(cls) -> Path:
        return CONFIG_DIR / "node_config.json"

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
            nodeRam = config_defaults.DEFAULT_RAM

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
            nodeMode = NodeMode.any

        return nodeMode

    @nodeMode.setter
    def nodeMode(self, value: int) -> None:
        self._raw["nodeMode"] = value

    @property
    def nodeId(self) -> int:
        nodeId = self.getOptValue("nodeId", int)

        if nodeId is None:
            nodeId = self.fetchNodeId()

        return nodeId

    @nodeId.setter
    def nodeId(self, value: int) -> None:
        self._raw["nodeId"] = value

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

    def validateRamField(self, ramLimit: int) -> Tuple[bool, int, str]:
        isValid = True
        message = ""

        if ramLimit < config_defaults.MINIMUM_RAM:
            isValid = False
            raise DockerConfigurationException(
                f"Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) "
                f"is higher than your current Docker desktop RAM limit ({ramLimit}GB). "
                "Please adjust resource limitations in Docker Desktop settings to match Node requirements."
            )

        defaultRamValue = int(min(max(config_defaults.MINIMUM_RAM, ramLimit), config_defaults.DEFAULT_RAM))

        if not isinstance(self._raw.get("nodeRam"), int):
            isValid = False
            message = (
                f"Invalid config \"nodeRam\" field type \"{type(self._raw.get('nodeRam'))}\". Expected: \"int\""
                f"Using default value of {defaultRamValue} GB"
            )

        if self.nodeRam < config_defaults.MINIMUM_RAM:
            isValid = False
            message = (
                f"WARNING: Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) "
                f"is higher than the configured value ({self._raw.get('nodeRam')}GB)"
                f"Overriding \"nodeRam\" field to match node RAM requirements."
            )

        if self.nodeRam > ramLimit:
            isValid = False
            message = (
                f"WARNING: RAM limit in Docker Desktop ({ramLimit}GB) "
                f"is lower than the configured value ({self._raw.get('nodeRam')}GB)"
                f"Overriding \"nodeRam\" field to limit in Docker Desktop."
            )

        return isValid, defaultRamValue, message

    def validateCPUCount(self, cpuLimit: int) -> Tuple[bool, int, str]:
        isValid = True
        message = ""
        defaultCPUCount = config_defaults.DEFAULT_CPU_COUNT if config_defaults.DEFAULT_CPU_COUNT <= cpuLimit else cpuLimit

        if not isinstance(self._raw.get("cpuCount"), int):
            isValid = False
            message = (
                f"Invalid config \"cpuCount\" field type \"{type(self._raw.get('cpuCount'))}\". Expected: \"int\""
                f"Using default value of {defaultCPUCount} cores"
            )

        if self.cpuCount > cpuLimit:
            isValid = False
            message = (
                f"WARNING: CPU limit in Docker Desktop ({cpuLimit}) "
                f"is lower than the configured value ({self._raw.get('cpuCount')})"
                f"Overriding \"cpuCount\" field to limit in Docker Desktop."
            )

        return isValid, cpuLimit, message

    def validateSWAPMemory(self, swapLimit: int) -> Tuple[bool, int, str]:
        isValid = True
        message = ""
        defaultSWAPMemory = config_defaults.DEFAULT_SWAP_MEMORY if config_defaults.DEFAULT_SWAP_MEMORY <= swapLimit else swapLimit

        if not isinstance(self._raw.get("nodeSwap"), int):
            isValid = False
            message = (
                f"Invalid config \"nodeSwap\" field type \"{type(self._raw.get('nodeSwap'))}\". Expected: \"int\""
                f"Using default value of {defaultSWAPMemory} GB"
            )

        if self.nodeSwap > swapLimit:
            isValid = False
            message = (
                f"WARNING: SWAP limit in Docker Desktop ({swapLimit}GB) "
                f"is lower than the configured value ({self.nodeSwap}GB)"
                f"Overriding \"nodeSwap\" field to limit in Docker Desktop."
            )

        return isValid, defaultSWAPMemory, message

    def _isConfigValid(self) -> Tuple[bool, List[str]]:
        isValid = True
        errorMessages = []
        cpuLimit, ramLimit = docker.getResourceLimits()
        swapLimit = docker.getDockerSwapLimit()

        if not isinstance(self._raw.get("nodeName"), str):
            isValid = False
            errorMessages.append("Invalid configuration. Missing required field \"nodeName\".")

        if not isinstance(self._raw.get("image"), str):
            isValid = False
            errorMessages.append("Invalid configuration. Missing required field \"image\".")

        if not isinstance(self._raw.get("nodeAccessToken"), str):
            isValid = False
            errorMessages.append("Invalid configuration. Missing required field \"nodeAccessToken\".")

        isRamValid, nodeRam, message = self.validateRamField(ramLimit)
        if not isRamValid:
            errorMessages.append(message)
            self.nodeRam = nodeRam

        isCPUCountValid, cpuCount, message = self.validateCPUCount(cpuLimit)
        if not isCPUCountValid:
            errorMessages.append(message)
            self.cpuCount = cpuCount

        isSWAPMemoryValid, nodeSwap, message = self.validateSWAPMemory(swapLimit)
        if not isSWAPMemoryValid:
            errorMessages.append(message)
            self.nodeSwap = nodeSwap

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

    def fetchNodeId(self) -> int:
        params = {
            "machine_name": f"={self.nodeName}"
        }

        response = networkManager.get("service", params)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to fetch node id.")

        responseJson = response.getJson(dict)
        data = responseJson.get("data")

        if not isinstance(data, list):
            raise TypeError(f"Invalid \"data\" type {type(data)}. Expected: \"list\"")

        if len(data) == 0:
            raise ValueError(f"Node with name \"{self.nodeName}\" not found.")

        nodeJson = data[0]
        if not isinstance(nodeJson, dict):
            raise TypeError(f"Invalid \"nodeJson\" type {type(nodeJson)}. Expected: \"dict\"")
        nodeId = nodeJson.get("id")
        if not isinstance(nodeId, str):
            raise TypeError(f"Invalid \"nodeId\" type {type(nodeId)}. Expected: \"str\"")

        self.nodeId = int(nodeId)
        self.save()
        return int(nodeId)