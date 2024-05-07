from pathlib import Path

import sys
import logging
import runpy

from coretex import _task
from coretex.networking import RequestFailedError


if __name__ == "__main__":
    taskRun, callback = _task.processRemote(sys.argv)

    try:
        _task._prepareForExecution(taskRun)
        _task.current_task_run.setCurrentTaskRun(taskRun)

        callback.onStart()

        logging.getLogger("coretexpylib").info(">> [Coretex] TaskRun execution started")
        logging.getLogger("coretexpylib").info(f"\tPython: {sys.executable}")

        entryPointDir = str(Path(taskRun.entryPoint).parent)
        if entryPointDir not in sys.path:
            sys.path.append(entryPointDir)

        _coretexPath = str(Path(__file__).resolve().parent)
        if _coretexPath in sys.path:
            sys.path.remove(_coretexPath)

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
