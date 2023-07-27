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

from typing import List, Optional
from pathlib import Path

import logging
import subprocess

from ..logging import LogSeverity


def logProcessOutput(output: bytes, severity: LogSeverity) -> None:
    decoded = output.decode("UTF-8")

    for line in decoded.split("\n"):
        # skip empty lines
        if line.strip() == "":
            continue

        # ignoring type for now, has to be fixed in coretexpylib
        logging.getLogger("coretexpylib").log(severity.stdSeverity, line)


class CommandException(Exception):
    pass


def command(args: List[str], ignoreOutput: bool = False, shell: bool = False) -> None:
    process = subprocess.Popen(
        args,
        shell = shell,
        cwd = Path(__file__).parent,
        stdout = None if ignoreOutput else subprocess.PIPE,
        stderr = None if ignoreOutput else subprocess.PIPE
    )

    returnCode: Optional[int] = None

    if ignoreOutput:
        returnCode = process.wait()
    else:
        stdout = process.stdout
        if stdout is None:
            commandArgs = " ".join(args)
            raise ValueError(f">> [Coretex] Something went wrong while trying to execute \"{commandArgs}\"")

        while (returnCode := process.poll()) is None:
            lines = stdout.readlines()
            logProcessOutput(b"".join(lines), LogSeverity.info)

        stderr = process.stderr
        if stderr is None:
            commandArgs = " ".join(args)
            raise ValueError(f">> [Coretex] Something went wrong while trying to execute \"{commandArgs}\"")

        lines = stderr.readlines()
        logProcessOutput(b"".join(lines), LogSeverity.warning if returnCode == 0 else LogSeverity.fatal)

    if returnCode != 0:
        commandArgs = " ".join(args)
        raise CommandException(f">> [Coretex] Falied to execute command \"{commandArgs}\". Exit code \"{returnCode}\"")
