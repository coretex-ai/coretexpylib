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

from __future__ import annotations

from typing import Optional, Any, List
from threading import Lock, Thread
from logging import LogRecord, StreamHandler
from concurrent.futures import ThreadPoolExecutor

import time
import sys
import logging

from .log import Log
from .log_severity import LogSeverity
from ..networking import networkManager, RequestType


# Logs from library that is being used for making api requests is causing project to freeze because
# logs inside requests library are going to be called while api request for log in coretexpylib is not finished
# so request will never be done and it will enter infinite loop
IGNORED_LOGGERS = [
    "urllib3.connectionpool",
    "coretexnode",
    "werkzeug"
]
MAX_WAIT_TIME_BEFORE_UPDATE = 5


class _LoggerUploadWorker(Thread):

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


class LogHandler(StreamHandler):

    """
        Custom StreamHandler which intercepts and stores all
        received logs from python std logging module until they
        are all uploaded to Coretex API
    """

    __instanceLock = Lock()
    __instance: Optional[LogHandler] = None

    @classmethod
    def instance(cls) -> LogHandler:
        if cls.__instance is None:
            with cls.__instanceLock:
                if cls.__instance is None:
                    cls.__instance = LogHandler(sys.stdout)

        return cls.__instance

    def __init__(self, stream: Any) -> None:
        super().__init__(stream)

        self.__uploadWorker = _LoggerUploadWorker()
        self.__uploadWorker.start()

    @property
    def taskRunId(self) -> Optional[int]:
        return self.__uploadWorker._taskRunId

    @taskRunId.setter
    def taskRunId(self, value: Optional[int]) -> None:
        self.__uploadWorker._taskRunId = value

    def __restartUploadWorker(self) -> None:
        if self.__uploadWorker.is_alive():
            raise RuntimeError(">> [Coretex] Upload worker is already running")

        old = self.__uploadWorker

        self.__uploadWorker = _LoggerUploadWorker()
        self.__uploadWorker._taskRunId = old._taskRunId
        self.__uploadWorker.start()

    def emit(self, record: LogRecord) -> None:
        super().emit(record)

        if self.taskRunId is None:
            return

        if record.name in IGNORED_LOGGERS:
            return

        if not self.__uploadWorker.is_alive():
            self.__restartUploadWorker()

        severity = LogSeverity.fromStd(record.levelno)
        log = Log.create(record.message, severity)

        self.__uploadWorker.add(log)

    def flushLogs(self) -> bool:
        """
            Uploads all currently stored logs to Coretex backend

            Returns
            -------
            bool -> True if the upload is successful, False otherwise
        """

        return self.__uploadWorker.uploadLogs()

    def reset(self) -> None:
        """
            Resets the internal state of the LogHandler
            Clears all pending logs
            Resets the upload worker thread
        """

        self.__uploadWorker.reset()
