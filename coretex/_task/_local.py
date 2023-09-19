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

from typing import Tuple, Optional, List, Dict, Any
from getpass import getpass

import logging
import os
import json
import sys

from tap import Tap

import psutil

from ._base_callback import TaskCallback
from .. import folder_manager
from ..coretex import TaskRun, TaskRunStatus, BaseParameter, validateParameters, parameter_factory
from ..networking import networkManager


class LocalTaskCallback(TaskCallback):

    def onStart(self) -> None:
        super().onStart()

        folder_manager.clearTempFiles()

    def onSuccess(self) -> None:
        super().onSuccess()

        self._taskRun.updateStatus(TaskRunStatus.completedWithSuccess)

    def onKeyboardInterrupt(self) -> None:
        super().onKeyboardInterrupt()

        logging.getLogger("coretexpylib").info(">> [Coretex] Stopping the run")

        self._taskRun.updateStatus(TaskRunStatus.stopping)

        taskRunProcess = psutil.Process(os.getpid())
        children = taskRunProcess.children(recursive = True)

        logging.getLogger("coretexpylib").debug(f">> [Coretex] Number of child processes: {len(children)}")

        for process in children:
            process.kill()

        for process in children:
            process.wait()

        self._taskRun.updateStatus(TaskRunStatus.stopped)

    def onException(self, exception: BaseException) -> None:
        super().onException(exception)

        self._taskRun.updateStatus(TaskRunStatus.completedWithError)


class LocalArgumentParser(Tap):

    username: Optional[str]
    password: Optional[str]

    projectId: int
    name: Optional[str]
    description: Optional[str]

    def configure(self) -> None:
        self.add_argument("--username", nargs = "?", type = str, default = None)
        self.add_argument("--password", nargs = "?", type = str, default = None)

        self.add_argument("--projectId", type = int)
        self.add_argument("--name", nargs = "?", type = str, default = None)
        self.add_argument("--description", nargs = "?", type = str, default = None)


def _readTaskRunConfig() -> List[BaseParameter]:
    parameters: List[BaseParameter] = []

    with open("./experiment.config", "rb") as configFile:
        configContent: Dict[str, Any] = json.load(configFile)
        parametersJson = configContent["parameters"]

        if not isinstance(parametersJson, list):
            raise ValueError(">> [Coretex] Invalid experiment.config file. Property 'parameters' must be an array")

        for parameterJson in parametersJson:
            parameter = parameter_factory.create(parameterJson)
            parameters.append(parameter)

    parameterValidationResults = validateParameters(parameters, verbose = True)
    if not all(parameterValidationResults.values()):
        # Using this to make the parameter errors more readable without scrolling through the console
        sys.exit(1)

    return parameters


def _processLocal(args: Optional[List[str]] = None) -> Tuple[int, TaskCallback]:
    parser, unknown = LocalArgumentParser().parse_known_args(args)

    if parser.username is not None and parser.password is not None:
        logging.getLogger("coretexpylib").info(">> [Coretex] Logging in with provided credentials")
        response = networkManager.authenticate(parser.username, parser.password)
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

    if not os.path.exists("experiment.config"):
        raise FileNotFoundError(">> [Coretex] \"experiment.config\" file not found")

    taskRun: TaskRun = TaskRun.runLocal(
        parser.projectId,
        parser.name,
        parser.description,
        [parameter.encode() for parameter in _readTaskRunConfig()]
    )

    logging.getLogger("coretexpylib").info(f">> [Coretex] Created local run with ID \"{taskRun.id}\"")
    taskRun.updateStatus(TaskRunStatus.preparingToStart)

    return taskRun.id, LocalTaskCallback(taskRun, response.json["refresh_token"])
