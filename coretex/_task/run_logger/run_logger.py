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

import logging
import traceback
import functools

from .upload_worker import LoggerUploadWorker
from ...logging import Log, LogSeverity
from ...networking import networkManager, RequestFailedError


def exceptionToString(exception: BaseException) -> str:
    tb = traceback.format_tb(exception.__traceback__)
    tb.append(str(exception))
    return "".join(tb)


def uploadTaskRunLogs(taskRunId: int, logs: List[Log]) -> bool:
    try:
        params = {
            "model_queue_id": taskRunId,
            "logs": [log.encode() for log in logs]
        }

        response = networkManager.post(
            "model-queue/add-console-log",
            params,
            timeout = (5, 600)  # connection timeout 5 seconds, log upload timeout 600 seconds
        )

        return not response.hasFailed()
    except RequestFailedError as ex:
        logging.getLogger("coretexpylib").error(f">> Failed to upload console logs to Coretex. Reason: {ex}")
        logging.getLogger("coretexpylib").debug(f">> Failed to upload console logs to Coretex. Reason: {ex}", exc_info = ex)

        return False


class RunLogger:

    NAME = "coretex-run"

    def __init__(self) -> None:
        self._logger = logging.getLogger(RunLogger.NAME)
        self._uploadWorker: Optional[LoggerUploadWorker] = None

    def attach(self, taskRunId: int) -> None:
        if self._uploadWorker is not None:
            raise ValueError("TaskRun is already attached to logger")

        self._uploadWorker = LoggerUploadWorker(functools.partial(uploadTaskRunLogs, taskRunId))
        self._uploadWorker.start()

    def reset(self) -> None:
        if self._uploadWorker is not None:
            self._uploadWorker.stop()
            self._uploadWorker.join()

            self._uploadWorker = None

    def flushLogs(self) -> bool:
        if self._uploadWorker is None:
            return False

        return self._uploadWorker.uploadLogs()

    def logProcessOutput(self, line: str, severity: Optional[LogSeverity] = None) -> None:
        if line.strip() == "":
            return

        log, _ = Log.parse(line)

        if severity is not None:
            log.severity = severity

        self._logger.log(log.severity.getLevel(), log.message)
        if self._uploadWorker is not None:
            self._uploadWorker.add(log)

    def log(self, severity: LogSeverity, message: str, exception: Optional[BaseException] = None) -> None:
        log = Log(severity, message)
        self._logger.log(severity.getLevel(), message)

        if self._uploadWorker is not None:
            self._uploadWorker.add(log)

        if exception is not None:
            self.log(severity, exceptionToString(exception))

    def debug(self, message: str, exception: Optional[BaseException] = None) -> None:
        self.log(LogSeverity.debug, message, exception)

    def info(self, message: str, exception: Optional[BaseException] = None) -> None:
        self.log(LogSeverity.info, message, exception)

    def warning(self, message: str, exception: Optional[BaseException] = None) -> None:
        self.log(LogSeverity.warning, message, exception)

    def error(self, message: str, exception: Optional[BaseException] = None) -> None:
        self.log(LogSeverity.error, message, exception)

    def critical(self, message: str, exception: Optional[BaseException] = None) -> None:
        self.log(LogSeverity.fatal, message, exception)

    warn = warning
    fatal = critical


runLogger = RunLogger()
