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

from typing import Optional, Tuple

from . import config_defaults
from .node import NodeConfiguration, DockerConfigurationException


def validateRamField(nodeConfig: NodeConfiguration, ramLimit: int) -> Optional[Tuple[int, str]]:
    if ramLimit < config_defaults.MINIMUM_RAM:
        raise DockerConfigurationException(
            f"Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) "
            f"is higher than your current Docker desktop RAM limit ({ramLimit}GB). "
            "Please adjust resource limitations in Docker Desktop settings to match Node requirements."
        )

    defaultRamValue = int(min(max(config_defaults.MINIMUM_RAM, ramLimit), config_defaults.DEFAULT_RAM))

    if not isinstance(nodeConfig._raw.get("ram"), int):
        message = (
            f"Invalid config \"ram\" field type \"{type(nodeConfig._raw.get('ram'))}\". Expected: \"int\""
            f"Using default value of {defaultRamValue} GB"
        )

        return defaultRamValue, message

    if nodeConfig.ram < config_defaults.MINIMUM_RAM:
        message = (
            f"WARNING: Minimum Node RAM requirement ({config_defaults.MINIMUM_RAM}GB) "
            f"is higher than the configured value ({nodeConfig._raw.get('ram')}GB)"
            f"Overriding \"ram\" field to match node RAM requirements."
        )

        return defaultRamValue, message

    if nodeConfig.ram > ramLimit:
        message = (
            f"WARNING: RAM limit in Docker Desktop ({ramLimit}GB) "
            f"is lower than the configured value ({nodeConfig._raw.get('ram')}GB)"
            f"Overriding \"ram\" field to limit in Docker Desktop."
        )

        return defaultRamValue, message

    return None

def validateCpuCount(nodeConfig: NodeConfiguration, cpuLimit: int) -> Optional[Tuple[int, str]]:
    defaultCpuCount = config_defaults.DEFAULT_CPU_COUNT if config_defaults.DEFAULT_CPU_COUNT <= cpuLimit else cpuLimit

    if not isinstance(nodeConfig._raw.get("cpuCount"), int):
        message = (
            f"Invalid config \"cpuCount\" field type \"{type(nodeConfig._raw.get('cpuCount'))}\". Expected: \"int\""
            f"Using default value of {defaultCpuCount} cores"
        )

        return defaultCpuCount, message

    if nodeConfig.cpuCount > cpuLimit:
        message = (
            f"WARNING: CPU limit in Docker Desktop ({cpuLimit}) "
            f"is lower than the configured value ({nodeConfig._raw.get('cpuCount')})"
            f"Overriding \"cpuCount\" field to limit in Docker Desktop."
        )

        return defaultCpuCount, message

    return None

def validateSwapMemory(nodeConfig: NodeConfiguration, swapLimit: int) -> Optional[Tuple[int, str]]:
    defaultSwapMemory = config_defaults.DEFAULT_SWAP_MEMORY if config_defaults.DEFAULT_SWAP_MEMORY <= swapLimit else swapLimit

    if not isinstance(nodeConfig._raw.get("swap"), int):
        message = (
            f"Invalid config \"swap\" field type \"{type(nodeConfig._raw.get('swap'))}\". Expected: \"int\""
            f"Using default value of {defaultSwapMemory} GB"
        )

        return defaultSwapMemory, message

    if nodeConfig.swap > swapLimit:
        message = (
            f"WARNING: SWAP limit in Docker Desktop ({swapLimit}GB) "
            f"is lower than the configured value ({nodeConfig.swap}GB)"
            f"Overriding \"swap\" field to limit in Docker Desktop."
        )

        return defaultSwapMemory, message

    return None