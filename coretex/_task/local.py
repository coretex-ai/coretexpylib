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
from pathlib import Path

import logging
import os
import json
import sys

from tap import Tap

import psutil

from .base_callback import TaskCallback
from ._worker import TaskRunWorker
from .. import folder_manager
from ..entities import TaskRun, TaskRunStatus, BaseParameter, BaseListParameter, validateParameters, parameter_factory, ParameterType
from ..networking import networkManager
from ..logging import LogHandler


EXPERIMENT_CONGIF_PATH = Path(".", "experiment.config")


class LocalTaskCallback(TaskCallback):

    def __init__(self, taskRun: TaskRun, refreshToken: str) -> None:
        super().__init__(taskRun)

        self._worker = TaskRunWorker(refreshToken, taskRun.id)

        self._logHandler = LogHandler.instance()
        self._logHandler.taskRunId = taskRun.id

    def onStart(self) -> None:
        self._worker.start()

        super().onStart()

        folder_manager.clearTempFiles()

    def onSuccess(self) -> None:
        super().onSuccess()

        self._taskRun.updateStatus(TaskRunStatus.completedWithSuccess)

        LogHandler.instance().flushLogs()
        LogHandler.instance().reset()

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

        LogHandler.instance().flushLogs()
        LogHandler.instance().reset()

    def onCleanUp(self) -> None:
        self._worker.stop()

        super().onCleanUp()


class LocalArgumentParser(Tap):

    username: Optional[str]
    password: Optional[str]

    projectId: int
    name: Optional[str]
    description: Optional[str]

    def __init__(self, parameters: List[BaseParameter]) -> None:
        self.parameters = parameters
        for parameter in parameters:
            # Dynamically add parameter names as attributes to the class, so they will
            # get parsed by parse_known_args
            setattr(self, parameter.name, None)

        super().__init__()

    def configure(self) -> None:
        self.add_argument("--username", nargs = "?", type = str, default = None)
        self.add_argument("--password", nargs = "?", type = str, default = None)

        self.add_argument("--projectId", type = int)
        self.add_argument("--name", nargs = "?", type = str, default = None)
        self.add_argument("--description", nargs = "?", type = str, default = None)

        for parameter in self.parameters:
            if parameter.dataType in [ParameterType.dataset, ParameterType.enum, ParameterType.enumList, ParameterType.imuVectors, ParameterType.range]:
                self.add_argument(f"--{parameter.name}", nargs = "?", type = parameter.overrideValue, default = None)
            elif isinstance(parameter, BaseListParameter):
                self.add_argument(f"--{parameter.name}", nargs = "+",  type = parameter.listTypes[0], default = None)
            else:
                self.add_argument(f"--{parameter.name}", nargs = "?", type = parameter.types[0], default = None)

    def getParameter(
        self,
        parameterName: str,
        default: Any
    ) -> Optional[Any]:

        parsedParameter = getattr(self, parameterName)
        if parsedParameter is None:
            return default

        return parsedParameter

    @classmethod
    def readTaskRunConfig(cls) -> List[BaseParameter]:
        parameters: List[BaseParameter] = []

        if not EXPERIMENT_CONGIF_PATH.exists():
            return []

        with EXPERIMENT_CONGIF_PATH.open() as configFile:
            configContent: Dict[str, Any] = json.load(configFile)
            parametersJson = configContent["parameters"]

            if not isinstance(parametersJson, list):
                raise ValueError(">> [Coretex] Invalid experiment.config file. Property 'parameters' must be an array")

            for parameterJson in parametersJson:
                parameter = parameter_factory.create(parameterJson)
                parameters.append(parameter)

        return parameters


def processLocal(args: Optional[List[str]] = None) -> Tuple[int, TaskCallback]:
    parameters = LocalArgumentParser.readTaskRunConfig()

    parser = LocalArgumentParser(parameters)
    parser.parse_args()

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

    for parameter in parameters:
        parameter.value = parser.getParameter(parameter.name, parameter.value)

    parameterValidationResults = validateParameters(parameters, verbose = True)
    if not all(parameterValidationResults.values()):
        # Using this to make the parameter errors more readable without scrolling through the console
        sys.exit(1)

    taskRun: TaskRun = TaskRun.runLocal(
        parser.projectId,
        parser.name,
        parser.description,
        [parameter.encode() for parameter in parameters]
    )

    logging.getLogger("coretexpylib").info(f">> [Coretex] Created local run with ID \"{taskRun.id}\"")
    taskRun.updateStatus(TaskRunStatus.preparingToStart)

    return taskRun.id, LocalTaskCallback(taskRun, response.json["refresh_token"])
