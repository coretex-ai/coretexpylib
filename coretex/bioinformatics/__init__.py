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

from typing import Optional, Union
from pathlib import Path

from .utils import CommandException, command


def cutadaptTrim(
    forwardFile: Union[str, Path],
    forwardOutput: Union[str, Path],
    forwardAdapter: str,
    reverseFile: Optional[Union[str, Path]] = None,
    reverseOutput: Optional[Union[str, Path]] = None,
    reverseAdapter: Optional[str] = None
) -> None:
    """
        Used to trim adapter sequences from sigle-end and paired-end sequencing reads

        Parameters
        ----------
        forwardFile : str
            Path to the file holding forward sequences
        forwardOutput : str
            Path to the output file for forward sequences
        forwardAdapter : str
            The adapter sequence for the forward reads
        reverseFile : Optional[str]
            Path to the file holding reverse sequences (pass for paired-end reads,
             otherwise only forward is required for single-end)
        reverseOutput : Optional[str]
            Path to the output file for reverse sequences (pass for paired-end reads,
             otherwise only forward is required for single-end)
        reverseAdapter : Optional[str]
            The adapter sequence for the reverse reads (pass for paired-end reads,
             otherwise only forward is required for single-end)
    """

    args: list[str] = [
        "cutadapt",
        "-o", str(forwardOutput),
        "-g", forwardAdapter,
    ]

    if reverseOutput is not None and reverseAdapter is not None:
        args.extend([
            "-p", str(reverseOutput),
            "-G", reverseAdapter
        ])

    args.append(str(forwardFile))
    if reverseFile is not None:
        args.append(str(reverseFile))

    command(args)
