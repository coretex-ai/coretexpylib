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

from typing import Callable, List

import logging
import sys

from .remote import processRemote
from .current_task_run import setCurrentTaskRun
from .. import folder_manager
from ..entities import TaskRun, TaskRunStatus
from ..logging import createFormatter, initializeLogger
from ..logging.severity import LogSeverity
from ..networking import RequestFailedError


def _initializeLogger(taskRun: TaskRun) -> None:
    # enable/disable verbose mode for taskRuns
    severity = LogSeverity.info
    verbose = taskRun.parameters.get("verbose", False)

    if verbose:
        severity = LogSeverity.debug

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setLevel(severity.getLevel())
    streamHandler.setFormatter(createFormatter(
        includeTime = False,
        includeLevel = False,
        includeColor = False,
        jsonOutput = True
    ))

    logPath = folder_manager.getRunLogsDir(taskRun.id) / "run.log"
    initializeLogger(severity, logPath, streamHandler)


def _prepareForExecution(taskRun: TaskRun) -> None:
    _initializeLogger(taskRun)

    taskRun.updateStatus(
        status = TaskRunStatus.inProgress,
        message = "Executing task."
    )


def initializeRTask(mainFunction: Callable[[TaskRun], None], args: List[str]) -> None:
    """
        Initializes and starts the R task as Coretex TaskRun

        Parameters
        ----------
        mainFunction : Callable[[ExecutingTaskRun], None]
            entry point function
        args : Optional[List[str]]
            list of command line arguments
    """

    taskRun, callback = processRemote(args)

    try:
        _prepareForExecution(taskRun)
        setCurrentTaskRun(taskRun)

        callback.onStart()

        logging.getLogger("coretexpylib").info("TaskRun execution started")
        mainFunction(taskRun)

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
