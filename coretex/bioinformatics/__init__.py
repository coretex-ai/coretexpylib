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

from typing import Optional, Union, List
from pathlib import Path

from ..utils import command
from ..entities import CustomDataset


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

    if isinstance(forwardFile, Path):
        forwardFile = str(forwardFile)

    if isinstance(forwardOutput, Path):
        forwardOutput = str(forwardOutput)

    if isinstance(reverseFile, Path):
        reverseFile = str(reverseFile)

    if isinstance(reverseOutput, Path):
        reverseOutput = str(reverseOutput)

    args: List[str] = [
        "cutadapt",
        "-o", forwardOutput,
        "-g", forwardAdapter,
    ]

    if reverseOutput is not None and reverseAdapter is not None:
        args.extend([
            "-p", reverseOutput,
            "-G", reverseAdapter
        ])

    args.append(forwardFile)
    if reverseFile is not None:
        args.append(reverseFile)

    command(args)


def isPairedEnd(dataset: CustomDataset) -> bool:
    """
        Check to see if the dataset has paired-end sequences, i.e. two fastq files
        per sample (excluding the metadata file)

        Parameters
        ----------
        dataset : CustomDataset
            Coretex dataset that will be checked for paired-end sequences

        Returns
        -------
        bool -> True if paired-end, False otherwise
    """

    for sample in dataset.samples:
        sample.unzip()

        if sample.name.startswith("_metadata"):
            continue

        if len(list(sample.path.glob("*.fastq*"))) != 2:
            return False

    return True
