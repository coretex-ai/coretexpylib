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

from typing import TypeVar, Generic, Type, Generator, Optional, Union, Any
from pathlib import Path

import logging
import zipfile

from .dataset import Dataset
from ..sample import LocalSample, AnyLocalSample


SampleType = TypeVar("SampleType", bound = "LocalSample")
SampleGenerator = Generator[SampleType, None, None]


def _generateZippedSamples(path: Path, sampleClass: Type[SampleType]) -> Generator[SampleType, None, None]:
    for samplePath in path.glob("*"):
        if not zipfile.is_zipfile(samplePath):
            continue

        yield sampleClass(samplePath)


class LocalDataset(Generic[SampleType], Dataset[SampleType]):

    """
        Represents the generic Local Dataset class for all
        LocalDataset classes \n
        Used for working with local datasets

        Properties
        ----------
        path : Path
            local path of dataset
        sampleClass : Type[SampleType]
            class of sample
        generator : Optional[SampleGenerator]
            sample generator
    """

    def __init__(self, path: Path, sampleClass: Type[SampleType], generator: Optional[SampleGenerator] = None) -> None:
        if generator is None:
            generator = _generateZippedSamples(path, sampleClass)

        self.__path = path
        self.__sampleClass = sampleClass

        self.name = path.stem
        self.samples = list(generator)

    @staticmethod
    def default(path: Path) -> 'LocalDataset':
        """
            Creates Local Dataset object

            Parameters
            ----------
            path : Path
                Local Dataset path

            Returns
            -------
            LocalDataset -> Local Dataset object
        """

        return LocalDataset(path, LocalSample)

    @staticmethod
    def custom(path: Path, generator: SampleGenerator) -> 'LocalDataset':
        """
            Creates Custom Local Dataset object

            Parameters
            ----------
            path : Path
                Local Dataset path
            generator : SampleGenerator
                sample generator

            Returns
            -------
            LocalDataset -> Local Dataset object
        """

        return LocalDataset(path, AnyLocalSample, generator)

    @property
    def path(self) -> Path:
        """
            Returns
            -------
            Path -> Local Dataset path
        """

        return self.__path

    def download(self, decrypt: bool = True, ignoreCache: bool = False) -> None:
        logging.getLogger("coretexpylib").warning(">> [Coretex] Local dataset cannot be downloaded")

    def add(self, samplePath: Union[Path, str], sampleName: Optional[str] = None, **metadata: Any) -> SampleType:
        if isinstance(samplePath, str):
            samplePath = Path(samplePath)

        sample = self.__sampleClass(samplePath)
        self.samples.append(sample)

        return sample
