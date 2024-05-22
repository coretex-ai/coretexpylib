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

from typing import Optional, Literal
from logging import Formatter, LogRecord

import json

from .severity import LogSeverity
from .utils import colorMessage


FormatStyle = Literal["%", "{", "$"]


class CTXFormatter(Formatter):

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: FormatStyle = "%",
        validate: bool = True,
        color: bool = True,
        jsonOutput: bool = True
    ) -> None:

        super().__init__(fmt, datefmt, style, validate)

        self.color = color
        self.jsonOutput = jsonOutput

    def format(self, record: LogRecord) -> str:
        # INFO -> Info, ERROR -> Error, etc...
        record.levelname = record.levelname.lower().capitalize()

        severity = LogSeverity.fromLevel(record.levelno)
        formatted = super().format(record)

        if self.color:
            formatted = colorMessage(severity, formatted)

        if self.jsonOutput:
            return json.dumps({
                "severity": severity.value,
                "message": formatted + "\n"
            })

        return formatted
