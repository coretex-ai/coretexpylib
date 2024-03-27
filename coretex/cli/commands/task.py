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

import click

from ..modules.user import initializeUserSession
from ..modules.utils import onBeforeCommandExecute
from ..modules.project_utils import isProjectSelected
from ...utils.process import command
from ..._task.local.task_config import readTaskConfig
from ...configuration import loadConfig
from ...entities import TaskRun, TaskRunStatus
from ..resources import LOCAL_EXEC_PATH


@click.command()
@onBeforeCommandExecute(initializeUserSession)
@onBeforeCommandExecute(isProjectSelected)
@click.argument("path", type = click.Path(exists = True, dir_okay = False))
@click.option("--name", type = str, default = None)
@click.option("--description", type = str, default = None)
@click.option("--snapshot", type = bool, default = False)
def run(path: str, name: Optional[str], description: Optional[str], snapshot: bool) -> None:
    config = loadConfig()
    parameters = readTaskConfig()

    taskRun: TaskRun = TaskRun.runLocal(
        config["projectId"],
        snapshot,
        name,
        description,
        [parameter.encode() for parameter in parameters],
        entryPoint = path
    )

    taskRun.updateStatus(TaskRunStatus.preparingToStart)
    taskRunId = taskRun.id

    command(
        [sys.executable,
         str(LOCAL_EXEC_PATH),
         "--taskRunId", str(taskRunId),
         "--refreshToken", config["refreshToken"],
         "--projectId", str(config["projectId"])],
        cwd = str(Path.cwd())
    )
