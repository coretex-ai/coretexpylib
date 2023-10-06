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

import os
import sys
import logging

import psutil

from ..base_callback import TaskCallback
from ..worker import TaskRunWorker
from ..logging import OutputInterceptor
from ... import folder_manager
from ...entities import TaskRun, TaskRunStatus


class LocalTaskCallback(TaskCallback):

    def __init__(self, taskRun: TaskRun, refreshToken: str) -> None:
        super().__init__(taskRun)

        self._worker = TaskRunWorker(refreshToken, taskRun.id)

        # Store sys values so they can be restored later
        self.__stdoutBackup = sys.stdout
        self.__stderrBackup = sys.stderr

        self._interceptor = OutputInterceptor(sys.stdout)
        self._interceptor.attachTo(taskRun)

        sys.stdout = self._interceptor

    def onStart(self) -> None:
        self._worker.start()

        super().onStart()

        folder_manager.clearTempFiles()

    def onSuccess(self) -> None:
        super().onSuccess()

        self._interceptor.flushLogs()
        self._interceptor.reset()

        self._taskRun.updateStatus(TaskRunStatus.completedWithSuccess)

    def onException(self, exception: BaseException) -> None:
        super().onException(exception)

        self._interceptor.flushLogs()
        self._interceptor.reset()

        self._taskRun.updateStatus(TaskRunStatus.completedWithError)

    def onKeyboardInterrupt(self) -> None:
        super().onKeyboardInterrupt()

        logging.getLogger("coretexpylib").info(">> [Coretex] Stopping the run")

        self._taskRun.updateStatus(TaskRunStatus.stopping)

        taskRunProcess = psutil.Process(os.getpid())
        children = taskRunProcess.children(recursive = True)

        logging.getLogger("coretexpylib").debug(f">> [Coretex] Number of child processes: {len(children)}")

        for process in children:
            process.kill()

        for process in children:
            process.wait()

        self._taskRun.updateStatus(TaskRunStatus.stopped)

    def onCleanUp(self) -> None:
        self._worker.stop()

        sys.stdout = self.__stdoutBackup
        sys.stderr = self.__stderrBackup

        super().onCleanUp()
