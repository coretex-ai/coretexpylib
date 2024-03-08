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

import sys
import runpy
import logging

import click

from ..modules.user import initializeUserSession
from ..modules.utils import onBeforeCommandExecute
from ..modules.project_utils import isProjectSelected
from ...configuration import loadConfig
from ... import _task
from ..._task.local.local import LocalTaskCallback
from ..._task.local.task_config import readTaskConfig
from ...networking import RequestFailedError
from ...entities import TaskRun, TaskRunStatus

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

    print(path, name, description, snapshot)

    taskRun: TaskRun = TaskRun.runLocal(
        config["projectId"],
        snapshot,
        name,
        description,
        [parameter.encode() for parameter in parameters],
        entryPoint = path,
    )

    # logging.getLogger("coretexpylib").info(f">> [Coretex] Created local run with ID \"{taskRun.id}\"")

    taskRun.updateStatus(TaskRunStatus.preparingToStart)
    taskRunId = taskRun.id
    print(taskRunId)
    callback = LocalTaskCallback(taskRun, config["refreshToken"])

    try:
        taskRun = _task._prepareForExecution(taskRunId)
        _task.current_task_run.setCurrentTaskRun(taskRun)

        callback.onStart()

        logging.getLogger("coretexpylib").info(">> [Coretex] TaskRun execution started")

        # Run the entry point script
        runpy.run_path(taskRun.entryPoint, {}, "__main__")

        callback.onSuccess()
    except RequestFailedError:
        callback.onNetworkConnectionLost()
    except KeyboardInterrupt:
        callback.onKeyboardInterrupt()
    except BaseException as ex:
        callback.onException(ex)

        # sys.exit is ok here, finally block is guaranteed to execute
        # due to how sys.exit is implemented (it internally raises SystemExit exception)
        sys.exit(1)
    finally:
        callback.onCleanUp()