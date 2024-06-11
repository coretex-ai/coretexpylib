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

from typing import Optional, TypeVar, Generic, List, Callable
from abc import ABC, abstractmethod
from pathlib import Path

from ..sample import Sample
from ..utils import isEntityNameValid


SampleType = TypeVar("SampleType", bound = "Sample")


class Dataset(ABC, Generic[SampleType]):

    """
        Represents the generic class Dataset
        Includes methods that can be used by any instance of Dataset
        and abstract methods that must be implemented by any subclass

        Properties
        ----------
        name : str
            name of dataset
        samples : List[SampleType]
            list of samples
    """

    name: str
    samples: List[SampleType]

    @property
    def count(self) -> int:
        """
            Returns
            -------
            int -> number of samples in this dataset
        """

        return len(self.samples)

    @property
    @abstractmethod
    def path(self) -> Path:
        pass

    @abstractmethod
    def download(self, decrypt: bool = True, ignoreCache: bool = False) -> None:
        pass

    def rename(self, name: str) -> bool:
        """
            Renames the dataset, if the provided name is
            different from the current name

            Parameters
            ----------
            name : str
                new dataset name

            Returns
            -------
            bool -> True if dataset was renamed, False if dataset was not renamed
        """

        if not isEntityNameValid(name):
            raise ValueError(">> [Coretex] Dataset name is invalid. Requirements: alphanumeric characters (\"a-z\", and \"0-9\") and dash (\"-\") with length between 3 to 50")

        if self.name == name:
            return False

        self.name = name
        return True

    def getSample(self, name: str) -> Optional[SampleType]:
        """
            Retrieves sample which matches the provided name

            Parameters
            ----------
            name : str
                name of sample

            Returns
            -------
            Optional[SampleType] -> sample object
        """

        for sample in self.samples:
            # startswith must be used since if we import sample
            # with the same name twice, the second one will have
            # suffix with it's serial number
            if sample.name.startswith(name):
                return sample

        return None

    def getSamples(self, filterFunc: Callable[[SampleType], bool]) -> List[SampleType]:
        filteredSamples: List[SampleType] = []

        for sample in self.samples:
            if filterFunc(sample):
                filteredSamples.append(sample)

        return filteredSamples
