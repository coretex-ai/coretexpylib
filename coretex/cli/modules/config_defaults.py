from pathlib import Path

import os

from .node_mode import NodeMode
from ...statistics import getAvailableRamMemory, getAvailableCpuCount


cpuCount = os.cpu_count()

DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"
DEFAULT_STORAGE_PATH = str(Path.home() / ".coretex")
DEFAULT_RAM_MEMORY = getAvailableRamMemory()
MINIMUM_RAM_MEMORY = 6
DEFAULT_SWAP_MEMORY = DEFAULT_RAM_MEMORY * 2
DEFAULT_SHARED_MEMORY = 2
DEFAULT_CPU_COUNT = getAvailableCpuCount()
DEFAULT_NODE_MODE = NodeMode.execution
DEFAULT_ALLOW_DOCKER = False
DEFAULT_NODE_SECRET = ""
DEFAULT_INIT_SCRIPT = ""
