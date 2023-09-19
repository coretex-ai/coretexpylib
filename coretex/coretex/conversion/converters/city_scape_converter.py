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

from typing import Any, Optional, List, Set, Dict
from pathlib import Path

import glob
import os
import json
import logging

import numpy as np

from ..base_converter import BaseConverter
from ...annotation import CoretexImageAnnotation, CoretexSegmentationInstance, BBox


class CityScapeConverter(BaseConverter):

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        super().__init__(datasetName, projectId, datasetPath)

        self.__baseImagePath = os.path.join(datasetPath, "leftImg8bit_trainvaltest", "leftImg8bit")
        self.__baseAnnotationsPaths = [
            os.path.join(datasetPath, "gtFine_trainvaltest", "gtFine", "train"),
            os.path.join(datasetPath, "gtFine_trainvaltest", "gtFine", "val")
        ]

        self.__imagePaths: List[str] = []
        self.__imagePaths.extend(glob.glob(f"{self.__baseImagePath}/train/*/*.png"))
        self.__imagePaths.extend(glob.glob(f"{self.__baseImagePath}/val/*/*.png"))

    def __annotationPathFor(self, imagePath: str) -> str:
        # Extract last 2 components of imagePath
        annotationName = os.path.sep.join(Path(imagePath).parts[-2:])

        # Replace image specific name with annotation name
        annotationName = annotationName.replace("leftImg8bit.png", "gtFine_polygons.json")

        for annotationsPath in self.__baseAnnotationsPaths:
            annotationPath = os.path.join(annotationsPath, annotationName)

            if os.path.exists(annotationPath):
                return annotationPath

        raise RuntimeError

    def _dataSource(self) -> List[str]:
        return self.__imagePaths

    def _extractLabels(self) -> Set[str]:
        labels: Set[str] = set()

        for imagePath in self.__imagePaths:
            annotationPath = self.__annotationPathFor(imagePath)

            with open(annotationPath, mode="r") as annotationFile:
                annotationData: Dict[str, Any] = json.load(annotationFile)

                for obj in annotationData["objects"]:
                    labels.add(obj["label"])

        return labels

    def __extractInstance(self, obj: Dict[str, Any]) -> Optional[CoretexSegmentationInstance]:
        label = obj["label"]

        coretexClass = self._dataset.classByName(label)
        if coretexClass is None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] Class: ({label}) is not a part of dataset")
            return None

        polygon = np.array(obj["polygon"]).flatten().tolist()

        return CoretexSegmentationInstance.create(
            coretexClass.classIds[0],
            BBox.fromPoly(polygon),
            [polygon]
        )

    def __extractImageAnnotation(self, imagePath: str, annotationData: Dict[str, Any]) -> None:
        imageName = Path(imagePath).stem
        width = annotationData["imgWidth"]
        height = annotationData["imgHeight"]

        coretexAnnotation = CoretexImageAnnotation.create(imageName, width, height, [])

        for obj in annotationData["objects"]:
            instance = self.__extractInstance(obj)
            if instance is None:
                continue

            coretexAnnotation.instances.append(instance)

        self._saveImageAnnotationPair(imagePath, coretexAnnotation)

    def _extractSingleAnnotation(self, imagePath: str) -> None:
        annotationPath = self.__annotationPathFor(imagePath)

        with open(annotationPath, mode="r") as annotationFile:
            annotationData: Dict[str, Any] = json.load(annotationFile)
            self.__extractImageAnnotation(imagePath, annotationData)
