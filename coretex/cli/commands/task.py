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

import click

from ... import folder_manager
from ..modules import user, utils, project_utils
from ..._task import TaskRunWorker, LoggerUploadWorker, executeProcess, readTaskConfig
from ...configuration import UserConfiguration
from ...entities import TaskRun, TaskRunStatus
from ...resources import PYTHON_ENTRY_POINT_PATH


class RunException(Exception):
    pass


@click.command()
@utils.onBeforeCommandExecute(user.initializeUserSession)
@click.argument("path", type = click.Path(exists = True, dir_okay = False))
@click.option("--name", type = str, default = None)
@click.option("--description", type = str, default = None)
@click.option("--snapshot", type = bool, default = False)
@click.option("--project", "-p", type = str)
def run(path: str, name: Optional[str], description: Optional[str], snapshot: bool, project: Optional[str]) -> None:
    userConfig = UserConfiguration()

    if userConfig.refreshToken is None:
        raise RunException(f"Failed to execute \"coretex run {path}\" command. Authenticate again using \"coretex login\" command and try again.")

    parameters = readTaskConfig()

    selectedProject = project_utils.getProject(project, userConfig)
    if selectedProject is None:
        return

    taskRun: TaskRun = TaskRun.runLocal(
        selectedProject.id,
        snapshot,
        name,
        description,
        [parameter.encode() for parameter in parameters],
        entryPoint = path
    )

    taskRun.updateStatus(TaskRunStatus.preparingToStart)

    with TaskRunWorker(userConfig.refreshToken, taskRun.id):
        loggerUploadWorker = LoggerUploadWorker(taskRun.id)
        loggerUploadWorker.start()

        command = [
            "python", str(PYTHON_ENTRY_POINT_PATH),
            "--taskRunId", str(taskRun.id),
            "--refreshToken", userConfig.refreshToken
        ]

        returnCode = executeProcess(
            command,
            loggerUploadWorker,
            captureErr = True
        )

    loggerUploadWorker.uploadLogs()
    if returnCode != 0:
        taskRun.updateStatus(TaskRunStatus.completedWithError)
    else:
        taskRun.updateStatus(TaskRunStatus.completedWithSuccess)

    folder_manager.clearTempFiles()
