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

    def unzip(self, ignoreCache: bool = False) -> None:
        super().unzip(ignoreCache)

        try:
            compressedSequencePath = getSequenceFile(Path(self.path), [".gz"])
            decompressedSequencePath = compressedSequencePath.parent / compressedSequencePath.stem

            if decompressedSequencePath.exists() and not ignoreCache:
                return

            file_utils.gzipDecompress(compressedSequencePath, decompressedSequencePath)
        except FileNotFoundError:
            pass
