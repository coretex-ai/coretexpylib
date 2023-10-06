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

from datetime import datetime

import sys
import logging
import faulthandler
import signal

from .current_task_run import setCurrentTaskRun
from .. import folder_manager
from ..entities import TaskRun
from ..utils import DATE_FORMAT


class TaskCallback:

    def __init__(self, taskRun: TaskRun) -> None:
        self._taskRun = taskRun

    def onStart(self) -> None:
        # Call "kill -30 task_run_process_id" to dump current stack trace of the TaskRun into the file
        # 30 == signal.SIGUSR1
        # Only works on *nix systems
        faultHandlerPath = folder_manager.logs / f"task_run_stacktrace_{self._taskRun.id}_{datetime.now().strftime(DATE_FORMAT)}.log"
        faulthandler.register(
            signal.SIGUSR1,
            file = faultHandlerPath.open("w"),
            all_threads = True
        )

    def onSuccess(self) -> None:
        logging.getLogger("coretexpylib").info("TaskRun finished successfully")

    def onException(self, exception: BaseException) -> None:
        logging.getLogger("coretexpylib").critical("TaskRun failed to finish due to an error")
        logging.getLogger("coretexpylib").debug(exception, exc_info = True)
        logging.getLogger("coretexpylib").critical(str(exception))

    def onKeyboardInterrupt(self) -> None:
        pass

    def onNetworkConnectionLost(self) -> None:
        folder_manager.clearTempFiles()

        sys.exit(1)

    def onCleanUp(self) -> None:
        try:
            from py3nvml import py3nvml
            py3nvml.nvmlShutdown()
        except:
            pass

        folder_manager.clearTempFiles()
        setCurrentTaskRun(None)
