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

from ..node import NodeMode
from ..statistics import getAvailableRamMemory


DOCKER_CONTAINER_NAME = "coretex_node"
DOCKER_CONTAINER_NETWORK = "coretex_node"
DEFAULT_STORAGE_PATH = str(Path.home() / ".coretex")
DEFAULT_RAM_MEMORY = getAvailableRamMemory()
MINIMUM_RAM_MEMORY = 6
DEFAULT_SWAP_MEMORY = DEFAULT_RAM_MEMORY * 2
DEFAULT_SHARED_MEMORY = 2
DEFAULT_CPU_COUNT = os.cpu_count()
DEFAULT_NODE_MODE = NodeMode.execution
DEFAULT_ALLOW_DOCKER = False
DEFAULT_NODE_SECRET = ""
DEFAULT_INIT_SCRIPT = ""
