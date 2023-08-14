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

from ..local_sample import LocalSample
from ....utils import file as file_utils


def getSequenceFile(directoryPath: Path, extensions: List[str]) -> Path:
    for path in directoryPath.iterdir():
        if path.suffix in extensions:
            return path

    raise FileNotFoundError(f">> [Coretex] {directoryPath} has no files with extensions \"{extensions}\"")


def getForwardSequenceFile(directoryPath: Path, extensions: List[str]) -> Path:
    for path in directoryPath.iterdir():
        if "_R1_" in path.name and path.suffix in extensions:
            return path

    raise FileNotFoundError(f">> [Coretex] {directoryPath} has no files with \"_R1_\" in name and extensions \"{extensions}\"")


def getReverseSequenceFile(directoryPath: Path, extensions: List[str]) -> Path:
    for path in directoryPath.iterdir():
        if "_R2_" in path.name and path.suffix in extensions:
            return path

    raise FileNotFoundError(f">> [Coretex] {directoryPath} has no files with \"_R2_\" in name and extensions \"{extensions}\"")


class LocalSequenceSample(LocalSample):

    """
        Represents the local custom Sample class
        which is used for working with Other Task locally
    """

    @classmethod
    def supportedExtensions(cls) -> List[str]:
        return [".fasta", ".fastq", ".fa", ".fq"]

    @property
    def sequencePath(self) -> Path:
        """
            Returns the path of the .fasta or .fastq sequence file
            contained inside the sample. If the sample contains gzip compressed
            sequences, you will have to call Sample.unzip method first otherwise
            calling Sample.sequencePath will raise an exception

            Raises
            ------
            FileNotFoundError -> if no .fasta, .fastq, .fq, or .fq files are found inside the sample
        """
        return getSequenceFile(Path(self.path), self.supportedExtensions())

    @property
    def forwardPath(self) -> Path:
        """
            Returns the path of the .fasta or .fastq forward sequence file
            contained inside the sample. "_R1_" must be present in the filename
            otherwise it will not be recongnized. If the sample contains gzip compressed
            sequences, you will have to call Sample.unzip method first otherwise
            calling Sample.sequencePath will raise an exception

            Raises
            ------
            FileNotFoundError -> if no .fasta, .fastq, .fq, or .fq files are found inside the sample
        """
        return getForwardSequenceFile(Path(self.path), self.supportedExtensions())

    @property
    def reversePath(self) -> Path:
        """
            Returns the path of the .fasta or .fastq sequence file
            contained inside the sample. "_R2_" must be present in the filename
            otherwise it will not be recongnized. If the sample contains gzip compressed
            sequences, you will have to call Sample.unzip method first otherwise
            calling Sample.sequencePath will raise an exception

            Raises
            ------
            FileNotFoundError -> if no .fasta, .fastq, .fq, or .fq files are found inside the sample
        """
        return getReverseSequenceFile(Path(self.path), self.supportedExtensions())

    def __unzipSingleEnd(self, ignoreCache: bool = False) -> None:
        super().unzip(ignoreCache)

        try:
            compressedSequencePath = getSequenceFile(Path(self.path), [".gz"])
            decompressedSequencePath = compressedSequencePath.parent / compressedSequencePath.stem

            if decompressedSequencePath.exists() and not ignoreCache:
                return

            file_utils.gzipDecompress(compressedSequencePath, decompressedSequencePath)
        except FileNotFoundError:
            pass

    def __unzipPairedEnd(self, ignoreCache: bool = False) -> None:
        super().unzip(ignoreCache)

        try:
            compressedForwardPath = getForwardSequenceFile(Path(self.path), [".gz"])
            compressedReversePath = getReverseSequenceFile(Path(self.path), [".gz"])

            for compressedSequencePath in [compressedForwardPath, compressedReversePath]:
                decompressedSequencePath = compressedSequencePath.parent / compressedSequencePath.stem

                if decompressedSequencePath.exists() and not ignoreCache:
                    return

                file_utils.gzipDecompress(compressedSequencePath, decompressedSequencePath)
        except FileNotFoundError:
            pass

    def unzip(self, ignoreCache: bool = False) -> None:
        self.__unzipPairedEnd(ignoreCache) if self.isPairedEnd() else self.__unzipSingleEnd(ignoreCache)

    def isPairedEnd(self) -> bool:
        """
            This function returns True if the sample holds paired-end reads and
            False if it holds single end. Files for paired-end reads must contain
            "_R1_" and "_R2_" in their names, otherwise an exception will be raised
            If the sample contains gzip compressed sequences, you will have to call
            Sample.unzip method first otherwise calling Sample.isPairedEnd will
            raise an exception

            Raises
            ------
            FileNotFoundError -> if no files meeting the requirements for either single-end
            or paired-end sequencing reads
        """

        extensions = self.supportedExtensions()
        for extension in extensions:
            listOfPaths = list(self.path.glob(f"*{extension}"))

            if len(listOfPaths) == 0:
                continue

            if len(listOfPaths) == 1:
                return False

            if len(listOfPaths) == 2:
                for path in listOfPaths:
                    if "_R1_" not in path.name and "_R2_" not in path.name:
                        raise FileNotFoundError(f">> [Coretex] Sample \"{self.name}\" has two files with extensions \"{extensions}\", but they do not contain \"_R1_\" and \"_R2_\" in their names marking them as paired-end reads")

        raise FileNotFoundError(f">> [Coretex] Invalid sequence sample \"{self.name}\". Could not determine sequencing type")
