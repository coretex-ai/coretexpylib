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

from pathlib import Path

import sys
import logging

from .entities import LogSeverity


def initializeLogger(severity: LogSeverity, logPath: Path) -> None:
    """
        Initializes python logging module

        Parameters
        ----------
        severity : LogSeverity
            Severity level of the logger
        logPath : Path
            File path where logs will be stored
    """

    formatter = logging.Formatter(
        fmt = "%(asctime)s %(levelname)s: %(message)s",
        datefmt= "%Y-%m-%d %H:%M:%S",
        style = "%",
    )

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(severity.stdSeverity)
    consoleHandler.setFormatter(formatter)

    fileHandler = logging.FileHandler(logPath)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)

    logging.basicConfig(
        level = logging.NOTSET,
        force = True,
        handlers = [
            consoleHandler,
            fileHandler
        ]
    )
