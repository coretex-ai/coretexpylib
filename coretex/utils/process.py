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

from typing import List, Optional, Tuple
from pathlib import Path

import logging
import subprocess

from ..entities import LogSeverity


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


def command(
    args: List[str],
    ignoreStdout: bool = False,
    ignoreStderr: bool = False,
    shell: bool = False,
    check: bool = True
) -> Tuple[int, str, str]:

    process = subprocess.Popen(
        args,
        shell = shell,
        cwd = Path(__file__).parent,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    stdOutStr = ""
    stdErrStr = ""

    returnCode: Optional[int] = None

    stdout = process.stdout
    stderr = process.stderr

    if stdout is None and not ignoreStdout:
        commandArgs = " ".join(args)
        raise ValueError(f">> [Coretex] Something went wrong while trying to execute \"{commandArgs}\"")

    while (returnCode := process.poll()) is None:
        if stdout is not None:
            line = stdout.readline()
            stdOutStr = "\n".join([stdOutStr, line.decode("utf-8")])
            if not ignoreStdout:
                logProcessOutput(line, LogSeverity.info)

    if stderr is None and not ignoreStderr:
        commandArgs = " ".join(args)
        raise ValueError(f">> [Coretex] Something went wrong while trying to execute \"{commandArgs}\"")

    if stderr is not None:
        lines = stderr.readlines()
        stdErrStr = b"".join(lines).decode("utf-8")
        if not ignoreStderr:
            logProcessOutput(b"".join(lines), LogSeverity.warning if returnCode == 0 else LogSeverity.fatal)

    if returnCode != 0 and check:
        commandArgs = " ".join(args)
        raise CommandException(f">> [Coretex] Failed to execute command \"{commandArgs}\". Exit code \"{returnCode}\"")

    return returnCode, stdOutStr, stdErrStr
