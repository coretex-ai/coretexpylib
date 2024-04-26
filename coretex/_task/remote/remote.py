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

from typing import Tuple, Optional, List

import json
import logging
import sys

from tap import Tap

from ..base_callback import TaskCallback
from ...networking import networkManager
from ...entities import TaskRun, secret_factory


class RemoteArgumentParser(Tap):

    refreshToken: str
    taskRunId: int
    decryptedSecrets: Optional[str]

    def configure(self) -> None:
        self.add_argument("--refreshToken", type = str)
        self.add_argument("--taskRunId", type = int)
        self.add_argument("--decryptedSecrets", nargs = "?", type = str, default = None)


def processRemote(args: Optional[List[str]] = None) -> Tuple[TaskRun, TaskCallback]:
    remoteArgumentParser, unknown = RemoteArgumentParser().parse_known_args(args)

    response = networkManager.authenticateWithRefreshToken(remoteArgumentParser.refreshToken)
    if response.hasFailed():
        raise RuntimeError(">> [Coretex] Failed to authenticate")

    taskRun: TaskRun = TaskRun.fetchById(remoteArgumentParser.taskRunId)

    if remoteArgumentParser.decryptedSecrets is not None:
        try:
            decryptedSecrets = json.loads(remoteArgumentParser.decryptedSecrets)
            if not isinstance(decryptedSecrets, dict):
                raise TypeError

            for key, value in decryptedSecrets.items():
                if isinstance(value, dict):
                    taskRun.parameters[key] = secret_factory.create(value)

                if isinstance(value, list):
                    taskRun.parameters[key] = [secret_factory.create(element) for element in value]
        except BaseException as ex:
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Failed to load decrypted secrets - \"{ex}\"", exc_info = ex)

    return taskRun, TaskCallback(taskRun)
