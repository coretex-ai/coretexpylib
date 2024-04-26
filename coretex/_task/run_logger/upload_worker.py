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

from typing import List, Callable
from threading import Thread, Event, RLock

import time
import logging

from ...logging import Log


MAX_WAIT_TIME_BEFORE_UPDATE = 5
UploadFunction = Callable[[List[Log]], bool]


class LoggerUploadWorker(Thread):

    """
        Not intended for outside use

        A worker thread which is constantly running and
        uploading logs to Coretex backend every 5 seconds

        If the upload request fails the wait time is doubled
    """

    def __init__(self, uploadFunction: UploadFunction) -> None:
        super().__init__()

        self.setDaemon(True)
        self.setName("LoggerUploadWorker")

        self.__uploadFunction = uploadFunction
        self.__stopped = Event()
        self.__lock = RLock()
        self.__waitTime = MAX_WAIT_TIME_BEFORE_UPDATE
        self.__pendingLogs: List[Log] = []

    @property
    def isStopped(self) -> bool:
        return self.__stopped.is_set()

    def stop(self) -> None:
        with self.__lock:
            self.__stopped.set()

    def add(self, log: Log) -> None:
        with self.__lock:
            if self.isStopped:
                return

            self.__pendingLogs.append(log)

    def uploadLogs(self) -> bool:
        with self.__lock:
            if self.isStopped:
                return False

            if len(self.__pendingLogs) == 0:
                return True

            # Uploads logs to Coretex using the provided function
            result = self.__uploadFunction(self.__pendingLogs)

            # Only clear logs if they were successfully uploaded to coretex
            if result:
                self.__pendingLogs.clear()

            return result

    def run(self) -> None:
        while not self.isStopped:
            time.sleep(self.__waitTime)

            try:
                success = self.uploadLogs()
            except BaseException as exception:
                logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to upload logs", exc_info = exception)
                success = False

            if success:
                # If upload of logs was success reset wait time
                self.__waitTime = MAX_WAIT_TIME_BEFORE_UPDATE
            else:
                # If upload of logs failed, double the wait time
                self.__waitTime *= 2
