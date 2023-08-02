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

from typing import Optional

from .utils import CommandException, command


def cutadaptTrim(
    forewardFile: str,
    forewardOutput: str,
    forewardAdapter: str,
    reverseFile: Optional[str] = None,
    reverseOutput: Optional[str] = None,
    reverseAdapter: Optional[str] = None
) -> None:

    args: list[str] = [
        "cutadapt",
        "-o", forewardOutput,
        "-g", forewardAdapter,
    ]

    if reverseOutput is not None and reverseAdapter is not None:
        args.extend([
            "-p", reverseOutput,
            "-G", reverseAdapter
        ])

    if reverseFile is not None:
        args.append(reverseFile)

    args.append(forewardFile)

    command(args)
