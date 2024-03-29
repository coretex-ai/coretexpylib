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
from io import StringIO

from .upload_worker import LoggerUploadWorker
from ...entities import Log, LogSeverity


class OutputInterceptor(StringIO):

    def __init__(self, stream: TextIO, taskRunId: int) -> None:
        super().__init__()

        self.stream = stream
        self.worker = LoggerUploadWorker(taskRunId)

        self.worker.start()

    def write(self, value: str) -> int:
        self.worker.add(Log.create(value.rstrip(), LogSeverity.info))

        self.stream.write(value)
        self.stream.flush()

        return super().write(value)

    def flushLogs(self) -> bool:
        return self.worker.uploadLogs()

    def stop(self) -> None:
        self.worker.stop()
