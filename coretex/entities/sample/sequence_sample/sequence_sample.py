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

from typing import Union
from pathlib import Path

from .local_sequence_sample import LocalSequenceSample
from ..network_sample import NetworkSample


class SequenceSample(NetworkSample, LocalSequenceSample):

    """
        Represents the local custom Sample class
        which is used for working with Other Task locally
    """

    def __init__(self) -> None:
        NetworkSample.__init__(self)

    @classmethod
    def isValidSequenceFile(cls, path: Union[Path, str]) -> bool:
        """
            Checks whether the file is a valid sequence file or not.
            File is a valid sequence file if it ends with any of these extensions:
                - .fasta
                - .fastq
                - .fa
                - .fq
        """

        if not isinstance(path, Path):
            path = Path(path)

        supportedExtensions = cls.supportedExtensions()
        supportedExtensions.extend([f"{extension}.gz" for extension in cls.supportedExtensions()])

        return any(path.name.endswith(extension) for extension in supportedExtensions)
