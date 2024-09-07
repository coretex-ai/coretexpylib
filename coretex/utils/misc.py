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

import os
import sys
import hashlib


def isCliRuntime() -> bool:
    executablePath = sys.argv[0]
    return (
        executablePath.endswith("/bin/coretex") and
        os.access(executablePath, os.X_OK)
    )


def generateSha256Checksum(path: Path) -> str:
    sha256 = hashlib.sha256()
    chunkSize = 64 * 1024  # 65536 bytes

    with path.open("rb") as file:
        while chunk := file.read(chunkSize):
            sha256.update(chunk)

    return sha256.hexdigest()
