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

from typing import Optional, Any
from threading import Lock
from logging import LogRecord, StreamHandler

import sys

from .log import Log
from .log_severity import LogSeverity
from ._upload_worker import LoggerUploadWorker


# Logs from library that is being used for making api requests is causing project to freeze because
# logs inside requests library are going to be called while api request for log in coretexpylib is not finished
# so request will never be done and it will enter infinite loop
IGNORED_LOGGERS = [
    "urllib3.connectionpool",
    "coretexnode",
    "werkzeug"
]


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

        self.__uploadWorker = LoggerUploadWorker()
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

        self.__uploadWorker = LoggerUploadWorker()
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
