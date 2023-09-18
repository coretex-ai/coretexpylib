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

from typing import Any, Final, Optional, List, Dict, Set

import glob
import os
import json
import logging

from ..base_converter import BaseConverter
from ...annotation import CoretexImageAnnotation, CoretexSegmentationInstance, BBox


class _CocoImageAnnotationData:

    def __init__(self, data: Dict[str, Any], imageInfo: Dict[str, Any]) -> None:
        self.data = data
        self.imageInfo = imageInfo


class COCOConverter(BaseConverter):

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        super().__init__(datasetName, projectId, datasetPath)

        self.__imagesPath: Final = os.path.join(datasetPath, "images")

        annotationsPath = os.path.join(datasetPath, "annotations")
        self.__fileNames: Final = glob.glob(os.path.join(annotationsPath, "*.json"))

    def _dataSource(self) -> List[_CocoImageAnnotationData]:
        fullAnnotationData: List[_CocoImageAnnotationData] = []

        for fileName in self.__fileNames:
            with open(fileName) as jsonFile:
                data = json.load(jsonFile)

                fullAnnotationData.extend([
                    _CocoImageAnnotationData(data, imageInfo)
                    for imageInfo in data["images"]
                ])

        return fullAnnotationData

    def _extractLabels(self) -> Set[str]:
        labels: Set[str] = set()

        for fileName in self.__fileNames:
            with open(fileName) as jsonFile:
                data = json.load(jsonFile)

                for category in data["categories"]:
                    labels.add(category["name"])

        return labels

    def __extractInstance(
        self,
        categories: List[Dict[str, Any]],
        annotation: Dict[str, Any]
    ) -> Optional[CoretexSegmentationInstance]:

        label: Optional[str] = None

        for category in categories:
            if category["id"] == annotation["category_id"]:
                label = category["name"]

        if label is None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] Invalid class: {label}")
            return None

        coretexClass = self._dataset.classByName(label)
        if coretexClass is None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] Class: ({label}) is not a part of dataset")
            return None

        bbox = BBox(*(annotation["bbox"]))

        if "segmentation" in annotation:
            segmentation = annotation["segmentation"]
        else:
            segmentation = [
                bbox.polygon
            ]

        return CoretexSegmentationInstance.create(
            coretexClass.classIds[0],
            bbox,
            segmentation
        )

    def _extractSingleAnnotation(self, annotationData: _CocoImageAnnotationData) -> None:
        imageName = annotationData.imageInfo["file_name"]
        width = annotationData.imageInfo["width"]
        height = annotationData.imageInfo["height"]

        imagePath = os.path.join(self.__imagesPath, imageName)
        if not os.path.exists(imagePath):
            return

        coretexAnnotation = CoretexImageAnnotation.create(imageName, width, height, [])

        for annotation in annotationData.data["annotations"]:
            if annotation["image_id"] != annotationData.imageInfo["id"]:
                continue

            instance = self.__extractInstance(annotationData.data["categories"], annotation)
            if instance is None:
                continue

            coretexAnnotation.instances.append(instance)

        self._saveImageAnnotationPair(imagePath, coretexAnnotation)
