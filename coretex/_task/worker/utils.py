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

from multiprocessing.connection import Connection

import logging

from ... import folder_manager
from ...utils import createFileHandler


def sendSuccess(conn: Connection, message: str) -> None:
    conn.send({
        "code": 0,
        "message": message
    })


def sendFailure(conn: Connection, message: str) -> None:
    conn.send({
        "code": 1,
        "message": message
    })


def initializeLogger(taskRunId: int) -> None:
    formatter = logging.Formatter(
        fmt = "%(asctime)s %(levelname)s: %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
        style = "%",
    )

    workerLogPath = folder_manager.getRunLogsDir(taskRunId) / "worker.log"
    fileHandler = createFileHandler(workerLogPath)

    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)

    logging.basicConfig(
        level = logging.NOTSET,
        force = True,
        handlers = [fileHandler]
    )
