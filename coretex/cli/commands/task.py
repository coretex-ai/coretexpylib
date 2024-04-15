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

from typing import Optional
from pathlib import Path

import sys
import logging

import click

from ..modules.user import initializeUserSession
from ..modules.utils import onBeforeCommandExecute
from ..modules.project_utils import isProjectSelected
from ..._task import TaskRunWorker, LoggerUploadWorker, executeProcess
from ..._task.local.task_config import readTaskConfig
from ...configuration import loadConfig
from ...entities import TaskRun, TaskRunStatus, Project
from ...resources import PYTHON_ENTRY_POINT_PATH


class RunException(Exception):
    pass


@click.command()
@onBeforeCommandExecute(initializeUserSession)
@onBeforeCommandExecute(isProjectSelected)
@click.argument("path", type = click.Path(exists = True, dir_okay = False))
@click.option("--name", type = str, default = None)
@click.option("--description", type = str, default = None)
@click.option("--snapshot", type = bool, default = False)
@click.option("--project", "-p", type = str)
def run(path: str, name: Optional[str], description: Optional[str], snapshot: bool, project: Optional[str]) -> None:
    config = loadConfig()
    parameters = readTaskConfig()

    if project is not None:
        projectId = Project.fetchByName(project).id
    else:
        projectId = config["projectId"]

    taskRun: TaskRun = TaskRun.runLocal(
        projectId,
        snapshot,
        name,
        description,
        [parameter.encode() for parameter in parameters],
        entryPoint = path
    )

    taskRun.updateStatus(TaskRunStatus.preparingToStart)

    with TaskRunWorker(config["refreshToken"], taskRun.id) as worker:
        loggerUploadWorker = LoggerUploadWorker(taskRun.id)
        returnCode = executeProcess(
        [
            sys.executable,
            str(PYTHON_ENTRY_POINT_PATH),
            "--taskRunId", str(taskRun.id),
            "--refreshToken", config["refreshToken"],
            "--projectId", str(config["projectId"])
        ],
        loggerUploadWorker,
        True,
        logging.getLogger("cli"),
        cwd=Path.cwd()
    )

    loggerUploadWorker.uploadLogs()
    if returnCode != 0:
        taskRun.updateStatus(TaskRunStatus.completedWithError)
    else:
        taskRun.updateStatus(TaskRunStatus.completedWithSuccess)
