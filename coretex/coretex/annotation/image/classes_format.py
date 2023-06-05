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

from __future__ import annotations

from typing import Optional, List, Dict, Set
from uuid import UUID

import uuid
import random

from ....codable import Codable, KeyDescriptor


class ImageDatasetClass(Codable):

    """
        Image Dataset class metadata

        Properties
        ----------
        classIds : List[UUID]
            list of all uuids connected to this class
        label : str
            name of the class
        color : str
            color of the class
    """

    classIds: List[UUID]
    label: str
    color: str

    def __init__(self, label: Optional[str] = None, color: Optional[str] = None):
        if label is None:
            label = ""

        if color is None:
            color = ""

        self.classIds = [uuid.uuid4()]
        self.label = label
        self.color = color

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["classIds"] = KeyDescriptor("ids", UUID, list)
        descriptors["label"] = KeyDescriptor("name")

        return descriptors

    @classmethod
    def generate(cls, labels: Set[str]) -> ImageDatasetClasses:
        """
            Generates list of Coretex classes based on provided
            labels (class names)

            Parameters
            ----------
            labels : Set[str]
                list of labels (class names)

            Returns
            -------
            ImageDatasetClasses -> list of ImageDatasetClass (Coretex class metadata) objects

            Example
            -------
            >>> from coretex import ImageDatasetClass
            \b
            >>> labels = {"car", "bicycle"}
            >>> imgDatasetClasses = ImageDatasetClass.generate(labels)
            >>> print(classes)
            [
                ImageDatasetClass(
                    classIds = [UUID("81add001-1c9c-4949-8b73-3599f1d0de9d")],
                    name = "car",
                    color = "#bcb86b"
                ),
                ImageDatasetClass(
                    classIds = [UUID("d710019b-f28f-40ab-aa65-e13df949beff")],
                    name = "bicycle",
                    color = "#cbc66b"
                )
            ]
        """

        colors: Set[str] = set()

        while len(colors) != len(labels):
            color = f'#{"%06x" % random.randint(0, 0xFFFFFF)}'
            colors.add(color)

        return ImageDatasetClasses(
            [cls(label, color) for label, color in zip(labels, colors)]
        )


class ImageDatasetClasses(List[ImageDatasetClass]):

    """
        List of Image Dataset class metadata

        Properties
        ----------
        labels : List[str]
            list of the classes names
    """

    @property
    def labels(self) -> List[str]:
        labels = [element.label for element in self]
        labels.sort()

        return labels

    def classById(self, classId: UUID) -> Optional[ImageDatasetClass]:
        """
            Retrieves a Image dataset class based on provided ID

            Parameters
            ----------
            classID : UUID
                id of class

            Returns
            -------
            Optional[ImageDatasetClasses] -> fetched class if provided ID
            is found in list of class IDs, None otherwise

            Examples
            --------
            >>> from coretex import ImageDataset
            \b
            >>> dataset = ImageDataset.fetchById(1023)
            >>> classObj = dataset.classes.classById(UUID("d710019b-f28f-40ab-aa65-e13df949beff"))
            \b
            >>> if classObj is not None:
                    print(classObj.classIds)
                    print(classObj.label)
                    print(classObj.color)
            UUID("d710019b-f28f-40ab-aa65-e13df949beff")
            "bicycle"
            "#d06df5"
        """

        for element in self:
            for other in element.classIds:
                if str(classId) == str(other):
                    return element

        return None

    def classByLabel(self, label: str) -> Optional[ImageDatasetClass]:
        """
            Retrieves a Image dataset class based on provided label

            Parameters
            ----------
            label : str
                name of class

            Returns
            -------
            Optional[ImageDatasetClasses] -> fetched class if provided label
            is found in list of class labels, None otherwise
        """

        for element in self:
            if element.label == label:
                return element

        return None

    def labelIdForClassId(self, classId: UUID) -> Optional[int]:
        """
            Retrieves a label ID based on provided class ID

            Parameters
            ----------
            classId : UUID
                id of class

            Returns
            -------
            Optional[int] -> label ID if provided class ID
            is found in list of class IDs, None otherwise

            Example
            -------
            >>> from coretex import ImageDataset
            \b
            >>> dataset = ImageDataset.fetchById(1023)
            >>> labelId = dataset.classes.labelIdForClassId(UUID("d710019b-f28f-40ab-aa65-e13df949beff"))
            >>> print(labelId)
            1

        """

        clazz = self.classById(classId)
        if clazz is None:
            return None

        try:
            return self.labels.index(clazz.label)
        except ValueError:
            return None

    def labelIdForClass(self, clazz: ImageDatasetClass) -> Optional[int]:
        """
            Retrieves a label ID based on provided ImageDatasetClass object

            Parameters
            ----------
            clazz : ImageDatasetClass
                Image Dataset class metadata object

            Returns
            -------
            Optional[int] -> label ID if provided class exists
            in a list of ImageDataset classes otherwise None

            Example
            -------
            >>> from coretex import ImageDatasetClass
            \b
            >>> dataset = ImageDataset.fetchById(1023)
            >>> labelId = dataset.classes.labelIdForClass(dataset.classes[0])
            >>> print(labelId)
            0
        """

        return self.labelIdForClassId(clazz.classIds[0])

    def exclude(self, excludedClasses: List[str]) -> None:
        """
            Excludes classes that are provided in excludedClasses list

            Parameters
            ----------
            excludedClasses : List[str]
                list of classes that will be excluded
        """

        classes = [
            element for element in self
            if element.label not in excludedClasses
        ]

        self.clear()
        self.extend(classes)
