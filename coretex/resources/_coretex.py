from typing import Union
from pathlib import Path

import sys
import logging
import runpy

from coretex import _task
from coretex.networking import RequestFailedError


if __name__ == "__main__":
    taskRunId, callback = _task.processRemote(sys.argv)

    try:
        taskRun = _task._prepareForExecution(taskRunId)
        _task.current_task_run.setCurrentTaskRun(taskRun)

        callback.onStart()

        logging.getLogger("coretexpylib").info(">> [Coretex] TaskRun execution started")
        logging.getLogger("coretexpylib").info(f"\tPython: {sys.executable}")

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
