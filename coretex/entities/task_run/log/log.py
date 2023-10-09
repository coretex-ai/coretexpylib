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

from typing import Dict
from typing_extensions import Self

import time

from .severity import LogSeverity
from ....utils import mathematicalRound
from ....codable import Codable, KeyDescriptor


class Log(Codable):

    """
        Represents a single Coretex console log

        timestamps : float
            timestamp of the log
        message : str
            message of the log
        severity : LogSeverity
            severity of the log
    """

    timestamp: float
    message: str
    severity: LogSeverity

    def __init__(self) -> None:
        super().__init__()

        # Here for backwards compatibility
        self.type = 1

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["message"] = KeyDescriptor("content")
        descriptors["severity"] = KeyDescriptor(pythonType = LogSeverity)

        return descriptors

    @classmethod
    def create(cls, message: str, severity: LogSeverity) -> Self:
        """
            Creates a new Log object with the current timestamp

            Parameters
            ----------
            message : str
                message of the log
            severity : LogSeverity
                severity of the log

            Returns
            -------
            Self -> Log object
        """

        log = cls()

        log.timestamp = mathematicalRound(time.time(), 6)
        log.message = message
        log.severity = severity

        return log

    @classmethod
    def coloredMessage(cls, message: str, severity: LogSeverity) -> str:
        fmt = "\033[%dm%s\033[0m"
        return fmt % (severity.color, message)
