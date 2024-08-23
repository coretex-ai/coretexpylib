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

from typing import List, Optional, Tuple
from pathlib import Path

from . import utils, config_defaults
from .base import BaseConfiguration, CONFIG_DIR
from ..utils import docker
from ..node import NodeMode
from ..networking import networkManager, NetworkRequestError


class NodeConfiguration(BaseConfiguration):

    @classmethod
    def getConfigPath(cls) -> Path:
        return CONFIG_DIR / "node_config.json"

    @property
    def name(self) -> str:
        return self.getValue("name", str)

    @name.setter
    def name(self, value: str) -> None:
        self._raw["name"] = value

    @property
    def accessToken(self) -> str:
        return self.getValue("accessToken", str)

    @accessToken.setter
    def accessToken(self, value: str) -> None:
        self._raw["accessToken"] = value

    @property
    def storagePath(self) -> str:
        return self.getValue("storagePath", str)

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
    def ram(self) -> int:
        ram = self.getOptValue("ram", int)

        if ram is None:
            ram = config_defaults.DEFAULT_RAM

        return ram

    @ram.setter
    def ram(self, value: int) -> None:
        self._raw["ram"] = value

    @property
    def swap(self) -> int:
        swap = self.getOptValue("swap", int)

        if swap is None:
            swap = config_defaults.DEFAULT_SWAP_MEMORY

        return swap

    @swap.setter
    def swap(self, value: int) -> None:
        self._raw["swap"] = value

    @property
    def sharedMemory(self) -> int:
        sharedMemory = self.getOptValue("sharedMemory", int)

        if sharedMemory is None:
            sharedMemory = config_defaults.DEFAULT_SHARED_MEMORY

        return sharedMemory

    @sharedMemory.setter
    def sharedMemory(self, value: int) -> None:
        self._raw["sharedMemory"] = value

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
    def mode(self) -> int:
        mode = self.getOptValue("mode", int)

        if mode is None:
            mode = NodeMode.any

        return mode

    @mode.setter
    def mode(self, value: int) -> None:
        self._raw["mode"] = value

    @property
    def id(self) -> int:
        id = self.getOptValue("id", int)

        if id is None:
            id = self.fetchNodeId()

        return id

    @id.setter
    def id(self, value: int) -> None:
        self._raw["id"] = value

    @property
    def allowDocker(self) -> bool:
        return self.getValue("allowDocker", bool)

    @allowDocker.setter
    def allowDocker(self, value: bool) -> None:
        self._raw["allowDocker"] = value

    @property
    def secret(self) -> Optional[str]:
        return self.getOptValue("secret", str)

    @secret.setter
    def secret(self, value: Optional[str]) -> None:
        self._raw["secret"] = value

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

    @property
    def heartbeatInterval(self) -> int:
        return self.getValue("heartbeatInterval", int, default = config_defaults.HEARTBEAT_INTERVAL)

    @heartbeatInterval.setter
    def heartbeatInterval(self, value: int) -> None:
        self._raw["heartbeatInterval"] = value

    def _isConfigValid(self) -> Tuple[bool, List[str]]:
        isValid = True
        errorMessages = []
        cpuLimit, ramLimit = docker.getResourceLimits()
        swapLimit = docker.getDockerSwapLimit()

        if not isinstance(self._raw.get("name"), str):
            isValid = False
            errorMessages.append("Invalid configuration. Missing required field \"name\".")

        if not isinstance(self._raw.get("image"), str):
            isValid = False
            errorMessages.append("Invalid configuration. Missing required field \"image\".")

        if not isinstance(self._raw.get("accessToken"), str):
            isValid = False
            errorMessages.append("Invalid configuration. Missing required field \"accessToken\".")

        validateRamField = utils.validateRamField(self, ramLimit)
        if isinstance(validateRamField, tuple):
            ram, message = validateRamField
            errorMessages.append(message)
            self.ram = ram

        validateCpuCount = utils.validateCpuCount(self, cpuLimit)
        if isinstance(validateCpuCount, tuple):
            cpuCount, message = validateCpuCount
            errorMessages.append(message)
            self.cpuCount = cpuCount

        validateSwapMemory = utils.validateSwapMemory(self, swapLimit)
        if isinstance(validateSwapMemory, tuple):
            swap, message = validateSwapMemory
            errorMessages.append(message)
            self.swap = swap

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
            "name": f"={self.name}"
        }

        response = networkManager.get("service/directory", params)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to fetch node id.")

        responseJson = response.getJson(dict)
        data = responseJson.get("data")

        if not isinstance(data, list):
            raise TypeError(f"Invalid \"data\" type {type(data)}. Expected: \"list\"")

        if len(data) == 0:
            raise ValueError(f"Node with name \"{self.name}\" not found.")

        nodeJson = data[0]
        if not isinstance(nodeJson, dict):
            raise TypeError(f"Invalid \"nodeJson\" type {type(nodeJson)}. Expected: \"dict\"")

        id = nodeJson.get("id")
        if not isinstance(id, int):
            raise TypeError(f"Invalid \"id\" type {type(id)}. Expected: \"int\"")

        self.id = int(id)
        self.save()

        return int(id)
