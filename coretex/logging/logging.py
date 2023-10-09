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
from pathlib import Path

import sys
import logging

from .formatter import CTXFormatter
from ..entities import LogSeverity


def _getFormatter(
    includeTime: bool = True,
    includeLevel: bool = True,
    includeColor: bool = True
) -> logging.Formatter:

    fmt: List[str] = []

    if includeTime:
        fmt.append("%(asctime)s")

    if includeLevel:
        fmt.append("%(levelname)s")

    if len(fmt) != 0:
        fmt[-1] = fmt[-1] + ":"

    fmt.append("%(message)s")

    return CTXFormatter(
        fmt = " ".join(fmt),
        datefmt= "%Y-%m-%d %H:%M:%S",
        style = "%",
        color = includeColor
    )


def initializeLogger(severity: LogSeverity, logPath: Path, formatConsole: bool = True) -> None:
    """
        Initializes python logging module

        Parameters
        ----------
        severity : LogSeverity
            Severity level of the logger
        logPath : Path
            File path where logs will be stored
        includeTime : bool
            Should datetime be included in logged message or not
    """

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(severity.stdSeverity)

    consoleFormatter = _getFormatter(includeTime = formatConsole, includeLevel = formatConsole)
    consoleHandler.setFormatter(consoleFormatter)

    fileHandler = logging.FileHandler(logPath)
    fileHandler.setLevel(logging.DEBUG)

    fileFormatter = _getFormatter(includeColor = False)
    fileHandler.setFormatter(fileFormatter)

    logging.basicConfig(
        level = logging.NOTSET,
        force = True,
        handlers = [
            consoleHandler,
            fileHandler
        ]
    )
