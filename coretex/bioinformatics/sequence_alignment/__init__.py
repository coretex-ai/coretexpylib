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

from typing import List, Tuple
from pathlib import Path

import subprocess
import logging

from ...coretex import CustomDataset
from ..utils import logProcessOutput


def command(args: List[str], ignoreOutput: bool = False) -> None:
    process = subprocess.Popen(
        args,
        shell = False,
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
        raise RuntimeError(f">> [Coretex] Falied to execute command. Returncode: {process.returncode}")


def indexCommand(bwaPath: Path, sequencePath: Path, prefix: Path) -> None:
    command([
        str(bwaPath.absolute()), "index",
        "-p", str(prefix.absolute()),
        str(sequencePath.absolute())
    ])


def alignCommand(bwaPath: Path, prefix: Path, sequencePath: Path, outputPath: Path) -> None:
    args = [
        str(bwaPath.absolute()), "mem",
        "-o", str(outputPath.absolute()),
        str(prefix.absolute()),
        str(sequencePath.absolute())
        ]

    command(args, True)


def sam2bamCommand(samtoolsPath: Path, samPath: Path, outputPath: Path) -> None:
    command([
        str(samtoolsPath.absolute()), "view",
        "-b", "-S", "-o",
        str(outputPath.absolute()),
        str(samPath.absolute())
    ])


def extractData(samtoolsPath: Path, file: Path) -> Tuple[List[int], List[int], List[int]]:
    scores: list[int] = []
    positions: list[int] = []
    sequenceLengths: list[int] = []

    args = [
        str(samtoolsPath.absolute()),
        "view", "-F", "256", "-F", "2048", "-F", "512",
        str(file.absolute())
    ]

    process = subprocess.Popen(
        args,
        shell = False,
        cwd = Path(__file__).parent,
        stdout = subprocess.PIPE
    )

    if process.stdout is None:
        raise RuntimeError(">> [Coretex] Output is none for samtools view command. Could not extract data")

    for line in process.stdout:
        fields = line.decode("UTF-8").strip().split("\t")
        scores.append(int(fields[4]))
        positions.append(int(fields[3]))
        sequenceLengths.append(len(fields[9]))

    return scores, positions, sequenceLengths


def chmodX(file: Path) -> None:
    command(["chmod", "+x", str(file.absolute())])


def loadFa(dataset: CustomDataset) -> List[Path]:
    inputFiles: list[Path] = []

    for sample in dataset.samples:
        sample.unzip()

        for file in Path(sample.path).iterdir():
            if file.suffix.startswith(".fa"):
                inputFiles.append(file)

    if len(inputFiles) == 0:
        raise ValueError(">> [Coretex] No sequence reads found")

    return inputFiles
