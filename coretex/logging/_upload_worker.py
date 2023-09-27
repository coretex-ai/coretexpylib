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

from typing import Optional, List
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

import time
import logging

from .log import Log
from ..networking import networkManager, RequestType


MAX_WAIT_TIME_BEFORE_UPDATE = 5


class LoggerUploadWorker(Thread):

    """
        Not intended for outside use

        A worker thread which is constantly running and
        uploading logs to Coretex backend every 5 seconds

        If the upload request fails the wait time is doubled
    """

    def __init__(self) -> None:
        super().__init__()

        self.setDaemon(True)
        self.setName("LoggerUploadWorker")

        # Task run for which the logs are uploaded
        self._taskRunId: Optional[int] = None

        self.__queue = ThreadPoolExecutor(max_workers = 1, thread_name_prefix = "LogQueue")
        self.__waitTime = MAX_WAIT_TIME_BEFORE_UPDATE
        self.__pendingLogs: List[Log] = []

    def add(self, log: Log) -> None:
        self.__queue.submit(self.__pendingLogs.append, log)

    def uploadLogs(self) -> bool:
        def worker() -> bool:
            if len(self.__pendingLogs) == 0:
                return True

            if self._taskRunId is None:
                raise ValueError(">> [Coretex] Tried to upload logs but no Task is being executed")

            response = networkManager.genericJSONRequest(
                endpoint = "model-queue/add-console-log",
                requestType = RequestType.post,
                parameters = {
                    "model_queue_id": self._taskRunId,
                    "logs": [log.encode() for log in self.__pendingLogs]
                }
            )

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
        while True:
            time.sleep(self.__waitTime)

            # Check if logger is attached to a run
            if self._taskRunId is None:
                continue

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

    def reset(self) -> None:
        self.__queue.shutdown(wait = True)
        self.__queue = ThreadPoolExecutor(max_workers = 1, thread_name_prefix = "LogQueue")

        self._taskRunId = None
        self.__waitTime = MAX_WAIT_TIME_BEFORE_UPDATE
        self.__pendingLogs.clear()
