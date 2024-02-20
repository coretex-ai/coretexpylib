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

from typing import List, Dict, Tuple, Optional
from typing_extensions import Self
from uuid import UUID
from math import cos, sin, radians

from PIL import Image, ImageDraw

import numpy as np

from .bbox import BBox
from .classes_format import ImageDatasetClasses
from ....codable import Codable, KeyDescriptor


SegmentationType = List[int]


def toPoly(segmentation: List[int]) -> List[Tuple[int, int]]:
    points: List[Tuple[int, int]] = []

    for index in range(0, len(segmentation) - 1, 2):
        points.append((segmentation[index], segmentation[index + 1]))

    return points


class CoretexSegmentationInstance(Codable):

    """
        Segmentation Instance class

        Properties
        ----------
        classID : UUID
            uuid of class
        bbox : BBox
            Bounding Box as a python class
        segmentations : List[SegmentationType]
            list of segmentations that define the precise boundaries of object
    """

    classId: UUID
    bbox: BBox
    segmentations: List[SegmentationType]

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["classId"] = KeyDescriptor("class_id", UUID)
        descriptors["bbox"] = KeyDescriptor("bbox", BBox)
        descriptors["segmentations"] = KeyDescriptor("annotations")

        return descriptors

    @classmethod
    def create(cls, classId: UUID, bbox: BBox, segmentations: List[SegmentationType]) -> Self:
        """
            Creates CoretexSegmentationInstance object with provided parameters

            Parameters
            ----------
            classID : UUID
                uuid of class
            bbox : BBox
                Bounding Box as a python class
            segmentations : List[SegmentationType]
                list of segmentations that define the precise boundaries of object

            Returns
            -------
            The created CoretexSegmentationInstance object
        """

        obj = cls()

        obj.classId = classId
        obj.bbox = bbox
        obj.segmentations = segmentations

        return obj

    def extractSegmentationMask(self, width: int, height: int) -> np.ndarray:
        """
            Generates segmentation mask based on provided
            width and height of image\n
            Pixel values are equal to class IDs

            Parameters
            ----------
            width : int
                width of image in pixels
            height : int
                height of image in pixels

            Returns
            -------
            np.ndarray -> segmentation mask represented as np.ndarray
        """

        image = Image.new("L", (width, height))

        for segmentation in self.segmentations:
            draw = ImageDraw.Draw(image)
            draw.polygon(toPoly(segmentation), fill = 1)

        return np.array(image)

    def extractBinaryMask(self, width: int, height: int) -> np.ndarray:
        """
            Works the same way as extractSegmentationMask function
            Values that are > 0 are capped to 1

            Parameters
            ----------
            width : int
                width of image in pixels
            height : int
                height of image in pixels

            Returns
            -------
            np.ndarray -> binary segmentation mask represented as np.ndarray
        """

        binaryMask = self.extractSegmentationMask(width, height)
        binaryMask[binaryMask > 0] = 1

        return binaryMask

    def centroid(self) -> Tuple[int, int]:
        """
            Calculates centroid of segmentations

            Returns
            -------
            Tuple[int, int] -> x, y coordinates of centroid
        """

        flattenedSegmentations = [element for sublist in self.segmentations for element in sublist]

        listCX = [value for index, value in enumerate(flattenedSegmentations) if index % 2 == 0]
        centerX = sum(listCX) // len(listCX)

        listCY = [value for index, value in enumerate(flattenedSegmentations) if index % 2 != 0]
        centerY = sum(listCY) // len(listCY)

        return centerX, centerY

    def centerSegmentations(self, newCentroid: Tuple[int, int]) -> None:
        """
            Centers segmentations to the specified center point

            Parameters
            ----------
            newCentroid : Tuple[int, int]
                x, y coordinates of centroid
            """

        newCenterX, newCenterY = newCentroid
        oldCenterX, oldCenterY = self.centroid()

        modifiedSegmentations: List[List[int]] = []

        for segmentation in self.segmentations:
            modifiedSegmentation: List[int] = []

            for i in range(0, len(segmentation), 2):
                x = segmentation[i] + (newCenterX - oldCenterX)
                y = segmentation[i+1] + (newCenterY - oldCenterY)

                modifiedSegmentation.append(x)
                modifiedSegmentation.append(y)

            modifiedSegmentations.append(modifiedSegmentation)

        self.segmentations = modifiedSegmentations

    def rotateSegmentations(
        self,
        degrees: int,
        origin: Optional[Tuple[int, int]] = None
    ) -> None:

        """
            Rotates segmentations of CoretexSegmentationInstance object

            Parameters
            ----------
            degrees : int
                degree of rotation
        """

        if origin is None:
            origin = self.centroid()

        rotatedSegmentations: List[List[int]] = []
        centerX, centerY = origin

        # because rotations with image and segmentations doesn't go in same direction
        # one of the rotations has to be inverted so they go in same direction
        theta = radians(-degrees)
        cosang, sinang = cos(theta), sin(theta)

        for segmentation in self.segmentations:
            rotatedSegmentation: List[int] = []

            for i in range(0, len(segmentation), 2):
                x = segmentation[i] - centerX
                y = segmentation[i + 1] - centerY

                newX = int(x * cosang - y * sinang) + centerX
                newY = int(x * sinang + y * cosang) + centerY

                rotatedSegmentation.append(newX)
                rotatedSegmentation.append(newY)

            rotatedSegmentations.append(rotatedSegmentation)

        self.segmentations = rotatedSegmentations


class CoretexImageAnnotation(Codable):

    """
        Image Annotation class

        Properties
        ----------
        name : str
            name of annotation class
        width : int
            width of annotation
        height : int
            height of annotation
        instances : List[CoretexSegmentationInstance]
            list of SegmentationInstance objects
    """

    name: str
    width: int
    height: int
    instances: List[CoretexSegmentationInstance]

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["instances"] = KeyDescriptor("instances", CoretexSegmentationInstance, list)

        return descriptors

    @classmethod
    def create(
        cls,
        name: str,
        width: int,
        height: int,
        instances: List[CoretexSegmentationInstance]
    ) -> Self:
        """
            Creates CoretexImageAnnotation object with provided parameters

            Parameters
            ----------
            name : str
                name of annotation class
            width : int
                width of annotation
            height : int
                height of annotation
            instances : List[CoretexSegmentationInstance]
                list of SegmentationInstance objects

            Returns
            -------
            The created CoretexImageAnnotation object
        """

        obj = cls()

        obj.name = name
        obj.width = width
        obj.height = height
        obj.instances = instances

        return obj

    def extractSegmentationMask(self, classes: ImageDatasetClasses) -> np.ndarray:
        """
            Generates segmentation mask of provided ImageDatasetClasses object

            Parameters
            ----------
            classes : ImageDatasetClasses
                list of dataset classes

            Returns
            -------
            np.ndarray -> segmentation mask represented as np.ndarray
        """

        image = Image.new("L", (self.width, self.height))

        for instance in self.instances:
            labelId = classes.labelIdForClassId(instance.classId)
            if labelId is None:
                continue

            for segmentation in instance.segmentations:
                if len(segmentation) == 0:
                    raise ValueError(f">> [Coretex] Empty segmentation")

                draw = ImageDraw.Draw(image)
                draw.polygon(toPoly(segmentation), fill = labelId + 1)

        return np.asarray(image)
