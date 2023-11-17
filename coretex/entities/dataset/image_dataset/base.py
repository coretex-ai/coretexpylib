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

from typing import TypeVar, Generic, Optional, List
from pathlib import Path

import json

from ...sample import Sample
from ...annotation import ImageDatasetClass, ImageDatasetClasses


SampleType = TypeVar("SampleType", bound = "Sample")


class BaseImageDataset(Generic[SampleType]):

    samples: List[SampleType]
    classes: ImageDatasetClasses
    path: Path

    @property
    def classesPath(self) -> Path:
        """
            Returns
            -------
            Path -> path to classes.json file
        """

        return self.path / "classes.json"

    def classByName(self, name: str) -> Optional[ImageDatasetClass]:
        for clazz in self.classes:
            if clazz.label == name:
                return clazz

        return None

    def _writeClassesToFile(self) -> None:
        self.path.mkdir(exist_ok = True)

        with open(self.classesPath, "w") as file:
            json.dump([clazz.encode() for clazz in self.classes], file)

    def saveClasses(self, classes: ImageDatasetClasses) -> bool:
        """
            Saves provided classes (including their color) to dataset.
            ImageDataset.classes property will be updated on successful save

            Parameters
            ----------
            classes : List[ImageDatasetClass]
                list of classes

            Returns
            -------
            bool -> True if dataset classes were saved, False if failed to save dataset classes

            Example
            -------
            >>> from coretex import ImageDatasetClass
            \b
            >>> labels = {"car", "bicycle", "person", "tree"}
            >>> imgDatasetClasses = ImageDatasetClass.generate(labels)
            >>> imageDatasetObj.saveClasses(imgDatasetClasses)
            True
        """

        self.classes = classes
        self._writeClassesToFile()

        return True
