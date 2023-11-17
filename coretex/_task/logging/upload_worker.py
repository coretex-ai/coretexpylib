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

from typing import List
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor

import time
import logging

from ...entities import Log
from ...networking import networkManager


MAX_WAIT_TIME_BEFORE_UPDATE = 5


class LoggerUploadWorker(Thread):

    """
        Not intended for outside use

        A worker thread which is constantly running and
        uploading logs to Coretex backend every 5 seconds

        If the upload request fails the wait time is doubled
    """

    def __init__(self, taskRunId: int) -> None:
        super().__init__()

        self.setDaemon(True)
        self.setName("LoggerUploadWorker")

        # Task run for which the logs are uploaded
        self.taskRunId = taskRunId

        self.__stopped = Event()
        self.__queue = ThreadPoolExecutor(max_workers = 1, thread_name_prefix = "LogQueue")
        self.__waitTime = MAX_WAIT_TIME_BEFORE_UPDATE
        self.__pendingLogs: List[Log] = []

    @property
    def isStopped(self) -> bool:
        return self.__stopped.is_set()

    def stop(self) -> None:
        self.__stopped.set()
        self.__queue.shutdown(wait = True)

    def add(self, log: Log) -> None:
        if self.isStopped:
            return

        self.__queue.submit(self.__pendingLogs.append, log)

    def uploadLogs(self) -> bool:
        if self.isStopped:
            return False

        def worker() -> bool:
            if len(self.__pendingLogs) == 0:
                return True

            response = networkManager.post("model-queue/add-console-log", {
                "model_queue_id": self.taskRunId,
                "logs": [log.encode() for log in self.__pendingLogs]
            })

            # Only clear logs if they were successfully uploaded to coretex
            if not response.hasFailed():
                self.__pendingLogs.clear()

            return not response.hasFailed()

        future = self.__queue.submit(worker)

        exception = future.exception()
        if exception is not None:
            logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to upload logs", exc_info = exception)
            return False

        return future.result()

    def run(self) -> None:
        while not self.isStopped:
            time.sleep(self.__waitTime)

            try:
                success = self.uploadLogs()
            except:
                success = False

            if success:
                # If upload of logs was success reset wait time
                self.__waitTime = MAX_WAIT_TIME_BEFORE_UPDATE
            else:
                # If upload of logs failed, double the wait time
                self.__waitTime *= 2
