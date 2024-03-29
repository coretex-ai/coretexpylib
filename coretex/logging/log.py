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

from typing import Dict, Any

import time

from ..severity import LogSeverity
from ..utils import mathematicalRound


class Log:

    """
        Represents a single Coretex console log

        timestamp : float
            timestamp of the log
        message : str
            message of the log
        severity : LogSeverity
            severity of the log
    """

    def __init__(self, severity: LogSeverity, message: str) -> None:
        self.timestamp = mathematicalRound(time.time(), 6)
        self.severity = severity
        self.message = message

        # Here for backwards compatibility
        self.type = 1

    def encode(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "content": self.message
        }
