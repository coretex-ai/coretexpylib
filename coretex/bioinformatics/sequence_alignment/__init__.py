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
import os

from ...utils import command, logProcessOutput, CommandException
from ...entities import CustomDataset, LogSeverity


def indexCommand(bwaPath: Path, sequencePath: Path, prefix: Path) -> None:
    """
        This function acts as a wrapper for the index command of BWA
        (Burrows-Wheeler Aligner). It is necessary to perform indexing
        on the reference sequence before alignment.

        Parameters
        ----------
        bwaPath : Path
            Path pointing to the bwa binary
        sequencePath : Path
            Path pointing to the reference sequence
        prefix : Path
            Path serving as the prefix for indexing. This command will
            generate 5 new files that are needed for alignment. These files will
            have the path "{prefix}.{suffix}", each with a different suffix / extension

        Example
        -------
        >>> from pathlib import Path
        >>> bwaPath = Path("tools/bwa")
        >>> sequencePath = Path("sequences/hg18.fa")
        >>> prefix = Path("output/hg18")
        >>> indexCommand(bwaPath, sequencePath, prefix)

        Link to BWA: https://bio-bwa.sourceforge.net
    """

    command([
        str(bwaPath.absolute()), "index",
        "-p", str(prefix.absolute()),
        str(sequencePath.absolute())
    ])


def alignCommand(
    bwaPath: Path,
    prefix: Path,
    sequencePath: Path,
    outputPath: Path,
    multithreading: bool = True
) -> None:

    """
        This function acts as a wrapper for the mem command of BWA
        (Burrows-Wheeler Aligner). It perfoms alignment of a given sequence read
        to the reference sequence and outputs a SAM file.

        Parameters
        ----------
        bwaPath : Path
            Path pointing to the bwa binary
        prefix : Path
            Path that serves as the prefix for the 5 files generated during indexing
        sequencePath : Path
            Path pointing to the sequence read file on which alignment should be performed
        outputPath : Path
            Path of the output file

        Example
        -------
        >>> from pathlib import Path
        >>> bwaPath = Path("tools/bwa")
        >>> prefix = Path("reference/hg18")
        >>> sequencePath = Path("input/R34D.fastq")
        >>> outputPath = Path("output/R34D.sam")
        >>> alignCommand(bwaPath, prefix, sequencePath, outputPath)

        Link to BWA: https://bio-bwa.sourceforge.net
    """

    args = [
        str(bwaPath.absolute()), "mem",
        "-o", str(outputPath.absolute())
    ]

    if multithreading:
        threads = os.cpu_count()
        if threads is not None:
            args.extend(["-t", str(threads)])

    args.extend([
        str(prefix.absolute()),
        str(sequencePath.absolute())
    ])

    command(args, True)


def sam2bamCommand(
    samtoolsPath: Path,
    samPath: Path,
    outputPath: Path,
    multithreading: bool = True
) -> None:

    """
        This function uses the CLI tool "samtools" to convert SAM files into their binary
        version, BAM.

        Parameters
        ----------
        samtoolsPath : Path
            Path pointing to the samtools binary
        samPath : Path
            Path pointing to the input .sam file
        outputPath : Path
            Path pointing to the output, .bam, file

        Example
        -------
        >>> from pathlib import Path
        >>> samtoolsPath = Path("tools/samtools")
        >>> samPath = Path("input/R34D.sam")
        >>> outputPath = Path("output/R34D.bam")
        >>> sam2bamCommand(samtoolsPath, samPath, outputPath)

        Link to samtools: http://htslib.org/
    """

    args = [
        str(samtoolsPath.absolute()), "view",
        "-b", "-S"
    ]

    if multithreading:
        threads = os.cpu_count()
        if threads is not None:
            args.extend(["--threads", str(threads - 1)])

    args.extend([
        "-o", str(outputPath.absolute()),
        str(samPath.absolute())
    ])

    command(args)


def extractData(samtoolsPath: Path, file: Path) -> Tuple[List[int], List[int], List[int]]:
    """
        Takes an aligned sequence file (SAM/BAM) and returns three lists holding
        MAPQ scores, leftmost position and sequence length for each read in the
        file. This is done using the samtools view command.

        Parameters
        ----------
        samtoolsPath : Path
            Path pointing to the samtools binary
        samPath : Path
            Path pointing to the input .sam or .bam file

        Example
        -------
        >>> from pathlib import Path
        >>> samtoolsPath = Path("tools/samtools")
        >>> file = Path("R34D.bam")
        >>> scores, positions, lengths = extractData(samtoolsPath, file)

        Link to samtools: http://htslib.org/
    """

    scores: List[int] = []
    positions: List[int] = []
    sequenceLengths: List[int] = []

    args = [
        str(samtoolsPath.absolute()),
        "view",
        "-F", "256", "-F", "2048", "-F", "512",  # Will ignore all duplicate reads
        str(file.absolute())
    ]

    process = subprocess.Popen(
        args,
        shell = False,
        cwd = Path(__file__).parent,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    while process.poll() is None:
        if process.stdout is None:
            continue

        stdout = process.stdout.readlines()

        for line in stdout:
            if len(line) > 0:
                fields = line.decode("UTF-8").strip().split("\t")
                scores.append(int(fields[4]))
                positions.append(int(fields[3]))
                sequenceLengths.append(len(fields[9]))

    if process.stderr is not None:
        for stderr in process.stderr:
            if len(stderr) > 0:
                if process.returncode == 0:
                    logProcessOutput(stderr, LogSeverity.warning)
                else:
                    logProcessOutput(stderr, LogSeverity.fatal)

    if process.returncode != 0:
        raise CommandException(f">> [Coretex] Falied to execute command. Returncode: {process.returncode}")

    return scores, positions, sequenceLengths


def chmodX(file: Path) -> None:
    command(["chmod", "+x", str(file.absolute())])


def loadFa(dataset: CustomDataset) -> List[Path]:
    inputFiles: List[Path] = []

    for sample in dataset.samples:
        sample.unzip()

        for file in Path(sample.path).iterdir():
            if file.suffix.startswith(".fa"):
                inputFiles.append(file)

    if len(inputFiles) == 0:
        raise ValueError(">> [Coretex] No sequence reads found")

    return inputFiles
