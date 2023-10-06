from typing import Callable, List

import logging
import sys

from .remote import processRemote
from .local import processLocal
from .current_task_run import setCurrentTaskRun
from .. import folder_manager
from ..entities import TaskRun, TaskRunStatus
from ..logging import LogSeverity, initializeLogger
from ..networking import RequestFailedError


def _prepareForExecution(taskRunId: int) -> TaskRun:
    taskRun: TaskRun = TaskRun.fetchById(taskRunId)

    # enable/disable verbose mode for taskRuns
    severity = LogSeverity.info
    verbose = taskRun.parameters.get("verbose", False)

    if verbose:
        severity = LogSeverity.debug

    logPath = folder_manager.logs / f"task_run_{taskRunId}.log"
    initializeLogger(severity, logPath)

    taskRun.updateStatus(
        status = TaskRunStatus.inProgress,
        message = "Executing task."
    )

    return taskRun


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

    try:
        taskRunId, callback = processRemote(args)
    except:
        taskRunId, callback = processLocal(args)

    try:
        taskRun = _prepareForExecution(taskRunId)
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
