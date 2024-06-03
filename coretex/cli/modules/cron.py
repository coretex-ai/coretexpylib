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

from ...utils import command
from ...configuration import DEFAULT_VENV_PATH


def getExisting() -> List[str]:
    _, output, error = command(["crontab", "-l"], ignoreStdout = True, ignoreStderr = True, check = False)
    if error is not None and "no crontab for" in error:
        return []
    if output is not None:
        return [line.strip() for line in output.split("\n") if line.strip()]

    raise ValueError("\"crontab\" is not installed. To enable automatic updates please install \"crontab\"")


def jobExists(script: str) -> bool:
    existingLines = getExisting()
    return any(line.endswith(script) for line in existingLines)


def scheduleJob() -> None:
    existingLines = getExisting()
    cronEntry = f"PATH={gitExecPath}:{dockerExecPath}\n*/5 * * * * {DEFAULT_VENV_PATH}/bin/coretex node update --auto >> {DEFAULT_VENV_PATH.parent}/out.txt  2>&1\n"
    existingLines.append(cronEntry)

    tempCronFilePath = DEFAULT_VENV_PATH.parent / "temp.cron"
    with tempCronFilePath.open("w") as tempCronFile:
        tempCronFile.write("\n".join(existingLines))

    command(["crontab", str(tempCronFilePath)])
    tempCronFilePath.unlink()
