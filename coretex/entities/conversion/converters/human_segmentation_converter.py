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

from typing import List, Set
from pathlib import Path

import os

from PIL import Image
from shapely.geometry import Polygon

import numpy as np
import skimage.measure

from ..base_converter import BaseConverter
from ...annotation import CoretexImageAnnotation, CoretexSegmentationInstance, ImageDatasetClass, BBox


class HumanSegmentationConverter(BaseConverter):

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        super().__init__(datasetName, projectId, datasetPath)

        self.__imagesPath = os.path.join(datasetPath, "images")
        self.__annotationsPath = os.path.join(datasetPath, "annotations")

        self.__imageNames = list(filter(
            lambda path: path.endswith("jpg"),
            os.listdir(self.__imagesPath))
        )

    @property
    def __backgroundClass(self) -> ImageDatasetClass:
        coretexClass = self._dataset.classByName("background")
        if coretexClass is None:
            raise ValueError(f">> [Coretex] Class: (background) is not a part of dataset")

        return coretexClass

    @property
    def __humanClass(self) -> ImageDatasetClass:
        coretexClass = self._dataset.classByName("human")
        if coretexClass is None:
            raise ValueError(f">> [Coretex] Class: (human) is not a part of dataset")

        return coretexClass

    def _dataSource(self) -> List[str]:
        return self.__imageNames

    def _extractLabels(self) -> Set[str]:
        return set(["background", "human"])

    def __extractPolygons(self, annotationPath: str, imageWidth: int, imageHeight: int) -> List[List[int]]:
        maskImage = Image.open(annotationPath)
        if maskImage is None:
            return []

        maskImage = maskImage.resize((imageWidth, imageHeight), Image.Resampling.LANCZOS)
        subMaskArray = np.asarray(maskImage, dtype = np.uint8)

        # prevent segmented objects from being equal to image width/height
        subMaskArray[:, 0] = 0
        subMaskArray[0, :] = 0
        subMaskArray[:, -1] = 0
        subMaskArray[-1, :] = 0

        contours = skimage.measure.find_contours(subMaskArray, 0.5)

        segmentations: List[List[int]] = []
        for contour in contours:
            for i in range(len(contour)):
                row, col = contour[i]
                contour[i] = (col - 1, row - 1)

            # Make a polygon and simplify it
            poly = Polygon(contour)

            if poly.geom_type == 'MultiPolygon':
                # If MultiPolygon, take the smallest convex Polygon containing all the points in the object
                poly = poly.convex_hull

            # Ignore if still not a Polygon (could be a line or point)
            if poly.geom_type == 'Polygon':
                segmentation = np.array(poly.exterior.coords).ravel().tolist()
                segmentations.append(segmentation)

        # sorts polygons by size, descending
        segmentations.sort(key=len, reverse=True)

        return segmentations

    def __extractInstances(self, annotationPath: str, imageWidth: int, imageHeight: int) -> List[CoretexSegmentationInstance]:
        polygons = self.__extractPolygons(annotationPath, imageWidth, imageHeight)
        if len(polygons) == 0:
            return []

        instances: List[CoretexSegmentationInstance] = []

        largestBBox = BBox.fromPoly(polygons[0])
        firstPolygon = Polygon(np.array(polygons[0]).reshape((-1, 2)))

        backgroundBoundingBox = BBox(0, 0, imageWidth, imageHeight)
        instances.append(CoretexSegmentationInstance.create(
            self.__backgroundClass.classIds[0],
            backgroundBoundingBox,
            [backgroundBoundingBox.polygon]
        ))

        instances.append(CoretexSegmentationInstance.create(
            self.__humanClass.classIds[0],
            largestBBox,
            [polygons[0]]
        ))

        for index in range(1, len(polygons)):
            currentBBox = BBox.fromPoly(polygons[index])
            currentPolygon = Polygon(np.array(polygons[index]).reshape((-1, 2)))

            instances.append(CoretexSegmentationInstance.create(
                self.__backgroundClass.classIds[0] if currentPolygon.intersects(firstPolygon) else self.__humanClass.classIds[0],
                currentBBox,
                [polygons[index]]
            ))

        return instances

    def _extractSingleAnnotation(self, imageName: str) -> None:
        imagePath = os.path.join(self.__imagesPath, imageName)
        annotationPath = os.path.join(self.__annotationsPath, f"{Path(imagePath).stem}.png")

        image = Image.open(imagePath)
        instances = self.__extractInstances(annotationPath, image.width, image.height)

        coretexAnnotation = CoretexImageAnnotation.create(imageName, image.width, image.height, instances)
        self._saveImageAnnotationPair(imagePath, coretexAnnotation)
