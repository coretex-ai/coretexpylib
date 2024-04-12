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

from datetime import datetime

from . import folder_manager
from .logging import initializeLogger, LogSeverity
from .configuration import CONFIG_DIR


def _initializeDefaultLogger() -> None:
    logName = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f%z")
    logPath = folder_manager.coretexpylibLogs.joinpath(logName).with_suffix(".log")

    initializeLogger(LogSeverity.info, logPath, jsonOutput = False)


def _initializeCLILogger() -> None:
    logName = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f%z")
    logPath = CONFIG_DIR / "logs"
    logPath.mkdir(exist_ok = True)

    initializeLogger(LogSeverity.info, logPath.joinpath(logName).with_suffix(".log"), jsonOutput = False)
