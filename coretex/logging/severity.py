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

from enum import IntEnum

import logging

class LogSeverity(IntEnum):

    """
        List of all log severities supported by Coretex
    """

    fatal   = 1
    error   = 2
    warning = 3
    info    = 4
    debug   = 5

    @property
    def color(self) -> int:
        """
            ANSI color of the log severity

            Returns
            -------
            str -> color
        """

        if self == LogSeverity.fatal:
            return 31  # red

        if self == LogSeverity.error:
            return 31  # red

        if self == LogSeverity.warning:
            return 33  # yellow

        if self == LogSeverity.info:
            return 97  # white

        if self == LogSeverity.debug:
            return 33  # yellow

        raise RuntimeError(">> [Coretex] Invalid enum value")

    def getLevel(self) -> int:
        """
            Converts Coretex log severity into the
            equivalent log level from python std module logging

            Returns
            -------
            int -> python std module logging level

            Example
            -------
            >>> from coretex.logging import LogSeverity
            \b
            >>> print(LogSeverity.info.stdSeverity)
            20
        """

        if self == LogSeverity.fatal:
            return logging.FATAL

        if self == LogSeverity.error:
            return logging.ERROR

        if self == LogSeverity.warning:
            return logging.WARNING

        if self == LogSeverity.info:
            return logging.INFO

        if self == LogSeverity.debug:
            return logging.DEBUG

        raise RuntimeError(">> [Coretex] Invalid enum value")

    @property
    def prefix(self) -> str:
        """
            Prefix of the log severity

            Returns
            -------
            str -> prefix
        """

        return self.name.capitalize()

    @staticmethod
    def fromLevel(logLevel: int) -> LogSeverity:
        """
            Converts python std module logging level
            into the equivalent log severity from coretex

            Returns
            -------
            LogSeverity -> Coretex log severity

            Example
            -------
            >>> import logging
            \b
            >>> from coretex.logging.log_severity import LogSeverity
            >>> logSeverityValue = LogSeverity.fromStd(logging.INFO)
            >>> print(logSeverityValue)
            LogSeverity.info
        """

        if logLevel == logging.FATAL:
            return LogSeverity.fatal

        if logLevel == logging.ERROR:
            return LogSeverity.error

        if logLevel == logging.WARNING:
            return LogSeverity.warning

        if logLevel == logging.INFO:
            return LogSeverity.info

        if logLevel == logging.DEBUG:
            return LogSeverity.debug

        raise ValueError(">> [Coretex] Invalid enum value")
