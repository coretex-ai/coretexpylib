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
from getpass import getpass

import logging
import sys

from .callback import LocalTaskCallback
from .arg_parser import LocalArgumentParser
from .task_config import readTaskConfig
from ...entities import TaskRun, TaskRunStatus, validateParameters
from ...networking import networkManager


def processLocal(args: Optional[List[str]] = None) -> Tuple[int, LocalTaskCallback]:
    # Parse and validate task parameters
    parameters = readTaskConfig()

    parser = LocalArgumentParser(parameters)
    namespace, _ = parser.parse_known_args(args)

    for parameter in parameters:
        parameter.value = parser.getParameter(parameter.name, parameter.value)

    parameterValidationResults = validateParameters(parameters, verbose = True)
    if not all(parameterValidationResults.values()):
        # Using this to make the parameter errors more readable without scrolling through the console
        sys.exit(1)

    # Authenticate
    if namespace.username is not None and namespace.password is not None:
        logging.getLogger("coretexpylib").info(">> [Coretex] Logging in with provided credentials")
        response = networkManager.authenticate(namespace.username, namespace.password)
    elif networkManager.hasStoredCredentials:
        logging.getLogger("coretexpylib").info(">> [Coretex] Logging in with stored credentials")
        response = networkManager.authenticateWithStoredCredentials()
    else:
        logging.getLogger("coretexpylib").info(">> [Coretex] Credentials not provided/stored")

        username = input("Enter your username: ")
        password = getpass("Enter your password: ")

        response = networkManager.authenticate(username, password)

    if response.hasFailed():
        raise RuntimeError(">> [Coretex] Failed to authenticate")

    # Create TaskRun
    taskRun: TaskRun = TaskRun.runLocal(
        namespace.projectId,
        namespace.saveSnapshot,
        namespace.name,
        namespace.description,
        [parameter.encode() for parameter in parameters]
    )

    logging.getLogger("coretexpylib").info(f">> [Coretex] Created local run with ID \"{taskRun.id}\"")
    taskRun.updateStatus(TaskRunStatus.preparingToStart)

    responseJson = response.getJson(dict)
    return taskRun.id, LocalTaskCallback(taskRun, responseJson["refresh_token"])
