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

from typing import Dict, List, Any
from typing_extensions import Self, override
from pathlib import Path

from .base import BaseImageDataset
from ..network_dataset import NetworkDataset
from ...sample import ImageSample
from ...annotation import ImageDatasetClass, ImageDatasetClasses
from ....codable import KeyDescriptor, Codable
from ....networking import networkManager, FileData, NetworkRequestError


class ClassDistribution(Codable):

    name: str
    color: str
    count: int


class ImageDataset(BaseImageDataset[ImageSample], NetworkDataset[ImageSample]):  # type: ignore

    """
        Represents the Image Dataset class \n
        Includes functionality for working with Image Datasets
        that are uploaded to Coretex.ai
    """

    classDistribution: List[ClassDistribution]

    def __init__(self) -> None:
        super().__init__(ImageSample)

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["samples"] = KeyDescriptor("sessions", ImageSample, list)
        descriptors["classes"] = KeyDescriptor("classes", ImageDatasetClass, ImageDatasetClasses)
        descriptors["classDistribution"] = KeyDescriptor("class_distribution", ClassDistribution, list)

        return descriptors

    @classmethod
    def fetchById(cls, objectId: int, **kwargs: Any) -> Self:
        obj = super().fetchById(objectId, **kwargs)

        response = networkManager.get(f"annotation-class?dataset_id={obj.id}")

        if not response.hasFailed():
            obj.classes = cls._decodeValue("classes", response.getJson(list))
            obj._writeClassesToFile()

        return obj

    def saveClasses(self, classes: ImageDatasetClasses) -> bool:
        parameters = {
            "dataset_id": self.id,
            "classes": [clazz.encode() for clazz in classes]
        }

        response = networkManager.post("annotation-class", parameters)
        if not response.hasFailed():
            return super().saveClasses(classes)

        return not response.hasFailed()

    @override
    def _uploadSample(self, samplePath: Path, sampleName: str, **metadata: Any) -> ImageSample:
        params = {
            "dataset_id": self.id
        }

        files = [
            FileData.createFromPath("file", samplePath)
        ]

        response = networkManager.formData("session/import", params, files)
        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to create image Sample from \"{samplePath}\"")

        return self._sampleType.decode(response.getJson(dict))
