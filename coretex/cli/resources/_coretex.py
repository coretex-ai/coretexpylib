from pathlib import Path

import sys
import logging
import runpy

from coretex import _task, TaskRun
from coretex._task.local.arg_parser import LocalArgumentParser
from coretex._task.local.task_config import readTaskConfig
from coretex._task.local.local import LocalTaskCallback
from coretex.entities import validateParameters
from coretex.networking import RequestFailedError


if __name__ == "__main__":
    parameters = readTaskConfig()

    parser = LocalArgumentParser(parameters)
    namespace, _ = parser.parse_known_args(sys.argv)

    taskRunId = namespace.taskRunId
    refreshToken = namespace.refreshToken

    for parameter in parameters:
        parameter.value = parser.getParameter(parameter.name, parameter.value)

    parameterValidationResults = validateParameters(parameters, verbose = True)
    if not all(parameterValidationResults.values()):
        # Using this to make the parameter errors more readable without scrolling through the console
        sys.exit(1)

    if not isinstance(taskRunId, int):
        raise TypeError(f"Invalid type of taskRunId expected \"int\", recieved: \"{type(taskRunId)}\"")

    if not isinstance(taskRunId, int):
        raise TypeError(f"Invalid type of taskRunId expected \"int\", recieved: \"{type(taskRunId)}\"")

    taskRun: TaskRun = TaskRun.fetchById(taskRunId)
    callback = LocalTaskCallback(taskRun, refreshToken)

    try:
        taskRun = _task._prepareForExecution(taskRunId)
        _task.current_task_run.setCurrentTaskRun(taskRun)

        callback.onStart()

        logging.getLogger("coretexpylib").info(">> [Coretex] TaskRun execution started")

        entryPointPath = Path(taskRun.entryPoint)

        # Run the entry point script
        runpy.run_path(str(entryPointPath), {}, "__main__")

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
