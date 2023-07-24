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

import logging
import subprocess


def logProcessOutput(output: bytes, severity: int) -> None:
    decoded = output.decode("UTF-8")

    for line in decoded.split("\n"):
        # skip empty lines
        if line.strip() == "":
            continue

        # ignoring type for now, has to be fixed in coretexpylib
        logging.getLogger("coretexpylib").log(severity, line)


class CommandException(Exception):
    pass


def command(args: List[str], ignoreOutput: bool = False, shell: bool = False) -> None:
    process = subprocess.Popen(
        args,
        shell = shell,
        cwd = Path(__file__).parent,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    while process.poll() is None:
        if process.stdout is None or process.stderr is None:
            continue

        stdout = process.stdout.readline()
        stderr = process.stderr.readline()

        if len(stdout) > 0 and not ignoreOutput:
            logProcessOutput(stdout, logging.INFO)

        if len(stderr) > 0 and not ignoreOutput:
            if process.returncode == 0:
                logProcessOutput(stderr, logging.INFO)
            else:
                logProcessOutput(stderr, logging.CRITICAL)

    if process.returncode != 0:
        raise CommandException(f">> [Coretex] Falied to execute command. Returncode: {process.returncode}")
