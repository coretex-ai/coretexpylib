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

from pathlib import Path

import json

from .base import BaseImageDataset
from ..local_dataset import LocalDataset
from ...sample import LocalImageSample
from ...annotation import ImageDatasetClass, ImageDatasetClasses


class LocalImageDataset(BaseImageDataset[LocalImageSample], LocalDataset[LocalImageSample]):  # type: ignore

    """
        Represents the Local Image Dataset class \n
        Includes functionality for working with local Image Datasets

        Properties
        ----------
        path : Path
            path to dataset
        sampleClass :
            Image Dataset Classes object
        classesPath : Path
            path to classes.json file
    """

    def __init__(self, path: Path) -> None:
        super().__init__(path, LocalImageSample)

        self.classes = ImageDatasetClasses()

        if self.classesPath.exists():
            with open(path / "classes.json") as file:
                value = json.load(file)
                self.classes = ImageDatasetClasses(
                    [ImageDatasetClass.decode(element) for element in value]
                )
