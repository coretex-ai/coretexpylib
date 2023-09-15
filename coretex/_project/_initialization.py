from typing import Callable, List

import logging
import sys

from ._remote import _processRemote
from ._local import _processLocal
from ._current_experiment import setCurrentTaskRun
from .. import folder_manager
from ..coretex import TaskRun, TaskRunStatus
from ..logging import LogHandler, LogSeverity, initializeLogger
from ..networking import RequestFailedError


def _prepareForExecution(taskRunId: int) -> TaskRun:
    taskRun: TaskRun = TaskRun.fetchById(taskRunId)

    customLogHandler = LogHandler.instance()
    customLogHandler.currentTaskRunId = taskRun.id

    # enable/disable verbose mode for taskRuns
    severity = LogSeverity.info
    verbose = taskRun.parameters.get("verbose", False)

    if verbose:
        severity = LogSeverity.debug

    logPath = folder_manager.logs / f"task_run_{taskRunId}.log"
    initializeLogger(severity, logPath)

    taskRun.updateStatus(
        status = TaskRunStatus.inProgress,
        message = "Executing project."
    )

    return taskRun


def initializeRProject(mainFunction: Callable[[TaskRun], None], args: List[str]) -> None:
    """
        Initializes and starts the R project as Coretex run

        Parameters
        ----------
        mainFunction : Callable[[ExecutingTaskRun], None]
            entry point function
        args : Optional[List[str]]
            list of command line arguments
    """

    try:
        taskRunId, callback = _processRemote(args)
    except:
        taskRunId, callback = _processLocal(args)

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
