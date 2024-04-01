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

from typing import Optional, List, Any
from threading import Thread
from pathlib import Path

import sys
import logging
import subprocess

import click

from ..resources import LOCAL_EXEC_PATH
from ..modules.user import initializeUserSession
from ..modules.utils import onBeforeCommandExecute
from ..modules.project_utils import isProjectSelected
from ..._task import TaskRunWorker, LoggerUploadWorker
from ..._task.local.task_config import readTaskConfig
from ...configuration import loadConfig
from ...entities import TaskRun, TaskRunStatus, Project, LogSeverity, Log


class RunException(Exception):
    pass


def _handleOutput(process: subprocess.Popen, worker: LoggerUploadWorker) -> None:
    stdout = process.stdout
    if stdout is None:
        raise ValueError("stdout is None for subprocess")

    while process.poll() is None:
        line: str = stdout.readline().decode("UTF-8")
        if line.strip() == "":
            continue

        worker.add(Log.create(line.rstrip(), LogSeverity.info))
        logging.info(line.rstrip())


def _handleError(process: subprocess.Popen, worker: LoggerUploadWorker, isEnabled: bool) -> None:
    stderr = process.stderr
    if stderr is None:
        raise ValueError("stderr is None for subprocess")

    lines: List[str] = []
    while process.poll() is None:
        line: str = stderr.readline().decode("UTF-8")
        if line.strip() == "":
            continue

        worker.add(Log.create(line.rstrip(), LogSeverity.error))
        lines.append(line.rstrip())

    # Dump stderr output at the end to perserve stdout order
    for line in lines:
        if isEnabled and process.returncode == 0:
            logging.warning(line)
        elif isEnabled:
            logging.error(line)
        else:
            # We always want to know what gets logged to stderr
            logging.debug(line)


def realtimeCommand(
    args: List[str],
    worker: Any,
    captureErr: bool,
    cwd: Path = Path(__file__).parent
) -> int:

    process = subprocess.Popen(
        args,
        shell = False,
        cwd = cwd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

     # Run a thread which captures process stdout and prints it out to Coretex.ai console
    Thread(
        target = _handleOutput,
        args = (process, worker),
        name = "Process stdout reader"
    ).start()

    if captureErr:
        # Run a thread which captures process stderr and dumps it out node log file
        Thread(
            target = _handleError,
            args = (process, worker, captureErr),
            name = "Process stderr reader"
        ).start()

    returnCode = process.wait()

    return returnCode


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
    taskRunId = taskRun.id

    taskRun.updateStatus(TaskRunStatus.preparingToStart)

    with TaskRunWorker(config["refreshToken"], taskRunId) as worker:
        loggerUploadWorker = LoggerUploadWorker(taskRunId)
        returnCode = realtimeCommand(
            [sys.executable,
            str(LOCAL_EXEC_PATH),
            "--taskRunId", str(taskRunId),
            "--refreshToken", config["refreshToken"],
            "--projectId", str(config["projectId"])],
            loggerUploadWorker,
            True,
            cwd = Path.cwd(),
        )

    loggerUploadWorker.uploadLogs()
    if returnCode != 0:
        taskRun.updateStatus(TaskRunStatus.completedWithError)
    else:
        taskRun.updateStatus(TaskRunStatus.completedWithSuccess)
