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
        self._worker = TaskRunWorker(refreshToken, taskRun.id)
        self._interceptor = OutputInterceptor(sys.stdout, taskRun.id)

        super().__init__(taskRun, self._interceptor)

    def _onTaskRunFinished(self, status: TaskRunStatus) -> None:
        self._worker.stop()

        self._interceptor.flushLogs()
        self._interceptor.stop()

        self._taskRun.updateStatus(status)

    def onStart(self) -> None:
        self._worker.start()

        super().onStart()

        folder_manager.clearTempFiles()

    def onSuccess(self) -> None:
        super().onSuccess()

        self._onTaskRunFinished(TaskRunStatus.completedWithSuccess)

    def onException(self, exception: BaseException) -> None:
        super().onException(exception)

        self._onTaskRunFinished(TaskRunStatus.completedWithError)

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

        self._onTaskRunFinished(TaskRunStatus.stopped)

    def onCleanUp(self) -> None:
        folder_manager.clearTempFiles()

        super().onCleanUp()
