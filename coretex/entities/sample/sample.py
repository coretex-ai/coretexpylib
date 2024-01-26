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

from typing import TypeVar, Generic, Union
from abc import ABC, abstractmethod
from zipfile import BadZipFile, ZipFile
from pathlib import Path

import shutil


SampleDataType = TypeVar("SampleDataType")


class Sample(ABC, Generic[SampleDataType]):

    """
        Represents the generic class Sample
        Includes methods that can be used by any instance of Sample
        and abstract methods that must be implemented by any subclass
    """

    name: str

    @property
    @abstractmethod
    def path(self) -> Path:
        pass

    @property
    @abstractmethod
    def zipPath(self) -> Path:
        pass

    @abstractmethod
    def download(self, ignoreCache: bool = False) -> None:
        """
            Downloads the Sample if it is an instance or a subclass of NetworkSample
            Ignored for instances and subclasses of LocalSample
        """
        pass

    def __unzipSample(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path)

        with ZipFile(self.zipPath) as zipFile:
            zipFile.extractall(self.path)

    def unzip(self, ignoreCache: bool = False) -> None:
        """
            Unzip sample zip file

            Parameters
            ----------
            ignoreCache : bool
                if set to false performs unzip action even if
                sample is previously unzipped
        """

        if self.path.exists() and not ignoreCache:
            return

        try:
            self.__unzipSample()
        except BadZipFile:
            # Delete invalid zip file
            self.zipPath.unlink()

            # Re-download
            self.download()

            # Try to unzip - if it fails again it should crash
            self.__unzipSample()

    @abstractmethod
    def load(self) -> SampleDataType:
        pass

    def joinPath(self, other: Union[Path, str]) -> Path:
        """
            Joins sample path and provided path

            Parameters
            ----------
            other : Union[Path, str]
                path for join

            Returns
            -------
            Path -> path created from sample path and provided path

            Example
            -------
            >>> print(sampleObj.joinPath("dummy.zip"))
            Path("path/to/sample/dummy.zip")
        """

        if isinstance(other, str):
            other = Path(other)

        return Path(self.path) / other
