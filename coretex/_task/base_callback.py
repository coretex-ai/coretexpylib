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

from typing import TextIO

import sys
import logging
import faulthandler
import signal

from .current_task_run import setCurrentTaskRun
from .. import folder_manager
from ..entities import TaskRun


class TaskCallback:

    def __init__(self, taskRun: TaskRun, outputStream: TextIO = sys.stdout) -> None:
        self._taskRun = taskRun

        # Store sys streams so they can be restored later
        self.__stdoutBackup = sys.stdout
        self.__stderrBackup = sys.stderr

        # Set sys output to new stream
        sys.stdout = outputStream
        sys.stderr = outputStream

    def _restoreStreams(self) -> None:
        sys.stdout = self.__stdoutBackup
        sys.stderr = self.__stderrBackup

    def onStart(self) -> None:
        # Call "kill -30 task_run_process_id" to dump current stack trace of the TaskRun into the file
        # 30 == signal.SIGUSR1
        # Only works on *nix systems

        faultHandlerPath = folder_manager.getRunLogsDir(self._taskRun.id) / "stacktrace.log"
        faulthandler.register(
            signal.SIGUSR1,
            file = faultHandlerPath.open("w"),
            all_threads = True
        )

    def onSuccess(self) -> None:
        logging.getLogger("coretexpylib").info(">> [Coretex] TaskRun finished successfully")

        self._restoreStreams()

    def onException(self, exception: BaseException) -> None:
        logging.getLogger("coretexpylib").critical(">> [Coretex] TaskRun failed to finish due to an error")
        logging.getLogger("coretexpylib").debug(exception, exc_info = True)
        logging.getLogger("coretexpylib").critical(str(exception))

        self._restoreStreams()

    def onKeyboardInterrupt(self) -> None:
        pass

    def onNetworkConnectionLost(self) -> None:
        sys.exit(1)

    def onCleanUp(self) -> None:
        # Flushes the internal buffers of logging module handlers
        # and other logging cleanup
        # IMPORTANT: do not use logging after calling this
        logging.shutdown()

        try:
            from py3nvml import py3nvml
            py3nvml.nvmlShutdown()
        except:
            pass

        setCurrentTaskRun(None)
