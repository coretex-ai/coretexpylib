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

from typing import TypeVar, Generic, Final
from pathlib import Path

import logging

from .sample import Sample


SampleDataType = TypeVar("SampleDataType")


class LocalSample(Generic[SampleDataType], Sample[SampleDataType]):

    """
        Represents a local sample object\n
        The purpose of this class is to provide a way to work with
        data samples that are stored locally

        Properties
        ----------
        name
            name of sample retrieved from path
        path : Path
            path to local sample
    """

    def __init__(self, path: Path) -> None:
        super().__init__()

        self.name: Final = path.stem
        self._path: Final = path

    @property
    def path(self) -> Path:
        """
            Returns
            -------
            Path -> path for local sample
        """

        return self._path.parent / self._path.stem

    @property
    def zipPath(self) -> Path:
        """
            Returns
            -------
            Path -> zip path for local sample
        """

        return self._path

    def download(self, ignoreCache: bool = False) -> None:
        logging.getLogger("coretexpylib").warning(">> [Coretex] Local sample cannot be downloaded")

    def load(self) -> SampleDataType:
        return super().load()  # type: ignore
