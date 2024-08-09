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

from typing import Optional, Tuple, Any

from . import config_defaults
from ..networking import networkManager, NetworkRequestError
from ..utils.docker import DockerConfigurationException


def validateRamField(ram: Optional[Any], ramLimit: int) -> Optional[Tuple[int, str]]:
    if ramLimit < config_defaults.MINIMUM_RAM:
        raise DockerConfigurationException(
            f"Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) "
            f"is higher than your current Docker desktop RAM limit ({ramLimit}GB). "
            "Please adjust resource limitations in Docker Desktop settings to match Node requirements."
        )

    defaultRamValue = int(min(max(config_defaults.MINIMUM_RAM, ramLimit), config_defaults.DEFAULT_RAM))

    if not isinstance(ram, int):
        message = (
            f"Invalid config \"ram\" field type \"{type(ram)}\". Expected: \"int\""
            f"Using default value of {defaultRamValue} GB"
        )

        return defaultRamValue, message

    if ram < config_defaults.MINIMUM_RAM:
        message = (
            f"WARNING: Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) "
            f"is higher than the configured value ({ram}GB)"
            f"Overriding \"ram\" field to match node RAM requirements."
        )

        return defaultRamValue, message

    if ram > ramLimit:
        message = (
            f"WARNING: RAM limit in Docker Desktop ({ramLimit}GB) "
            f"is lower than the configured value ({ram}GB)"
            f"Overriding \"ram\" field to limit in Docker Desktop."
        )

        return defaultRamValue, message

    return None

def validateCpuCount(cpuCount: Optional[Any], cpuLimit: int) -> Optional[Tuple[int, str]]:
    defaultCpuCount = config_defaults.DEFAULT_CPU_COUNT if config_defaults.DEFAULT_CPU_COUNT <= cpuLimit else cpuLimit

    if not isinstance(cpuCount, int):
        message = (
            f"Invalid config \"cpuCount\" field type \"{type(cpuCount)}\". Expected: \"int\""
            f"Using default value of {defaultCpuCount} cores"
        )

        return defaultCpuCount, message

    if cpuCount > cpuLimit:
        message = (
            f"WARNING: CPU limit in Docker Desktop ({cpuLimit}) "
            f"is lower than the configured value ({cpuCount})"
            f"Overriding \"cpuCount\" field to limit in Docker Desktop."
        )

        return defaultCpuCount, message

    return None

def validateSwapMemory(swap: Optional[Any], swapLimit: int) -> Optional[Tuple[int, str]]:
    defaultSwapMemory = config_defaults.DEFAULT_SWAP_MEMORY if config_defaults.DEFAULT_SWAP_MEMORY <= swapLimit else swapLimit

    if not isinstance(swap, int):
        message = (
            f"Invalid config \"swap\" field type \"{type(swap)}\". Expected: \"int\""
            f"Using default value of {defaultSwapMemory} GB"
        )

        return defaultSwapMemory, message

    if swap > swapLimit:
        message = (
            f"WARNING: SWAP limit in Docker Desktop ({swapLimit}GB) "
            f"is lower than the configured value ({swap}GB)"
            f"Overriding \"swap\" field to limit in Docker Desktop."
        )

        return defaultSwapMemory, message

    return None


def fetchNodeId(name: str) -> int:
    params = {
        "name": f"={name}"
    }

    response = networkManager.get("service/directory", params)
    if response.hasFailed():
        raise NetworkRequestError(response, "Failed to fetch node id.")

    responseJson = response.getJson(dict)
    data = responseJson.get("data")

    if not isinstance(data, list):
        raise TypeError(f"Invalid \"data\" type {type(data)}. Expected: \"list\"")

    if len(data) == 0:
        raise ValueError(f"Node with name \"{name}\" not found.")

    nodeJson = data[0]
    if not isinstance(nodeJson, dict):
        raise TypeError(f"Invalid \"nodeJson\" type {type(nodeJson)}. Expected: \"dict\"")

    id = nodeJson.get("id")
    if not isinstance(id, int):
        raise TypeError(f"Invalid \"id\" type {type(id)}. Expected: \"int\"")

    return id
