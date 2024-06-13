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

from enum import IntEnum

import requests

from .cron import jobExists, scheduleJob


UPDATE_SCRIPT_NAME = "update_node.py"


class NodeStatus(IntEnum):

    inactive     = 1
    active       = 2
    busy         = 3
    deleted      = 4
    reconnecting = 5


def activateAutoUpdate() -> None:
    if not jobExists(UPDATE_SCRIPT_NAME):
        scheduleJob(UPDATE_SCRIPT_NAME)


def getNodeStatus() -> NodeStatus:
    try:
        response = requests.get(f"http://localhost:21000/status", timeout = 1)
        status = response.json()["status"]
        return NodeStatus(status)
    except:
        return NodeStatus.inactive
