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

import os
import json
import glob
import logging

import numpy as np

from ..base_converter import BaseConverter
from ...annotation import CoretexImageAnnotation, CoretexSegmentationInstance, BBox


class LabelMeConverter(BaseConverter):

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        super().__init__(datasetName, projectId, datasetPath)

        self.__imagesPath = os.path.join(datasetPath, "images")

        annotations = os.path.join(datasetPath, "annotations")
        self.__fileNames = glob.glob(os.path.join(annotations, "*.json"))

    def _dataSource(self) -> List[str]:
        return self.__fileNames

    def _extractLabels(self) -> Set[str]:
        labels: Set[str] = set()

        for fileName in self.__fileNames:
            with open(fileName) as jsonFile:
                data = json.load(jsonFile)

                for shape in data["shapes"]:
                    labels.add(shape["label"])

        return labels

    def __extractInstance(self, shape: Dict[str, Any]) -> Optional[CoretexSegmentationInstance]:
        label = shape["label"]

        coretexClass = self._dataset.classByName(label)
        if coretexClass is None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] Class: ({label}) is not a part of dataset")
            return None

        points: List[int] = np.array(shape["points"]).flatten().tolist()
        bbox = BBox.fromPoly(points)

        return CoretexSegmentationInstance.create(coretexClass.classIds[0], bbox, [points])

    def __extractImageAnnotation(self, imageAnnotation: Dict[str, Any]) -> None:
        imageName = Path(imageAnnotation["imagePath"]).stem
        imageName = f"{imageName}.jpg"

        width = imageAnnotation["imageWidth"]
        height = imageAnnotation["imageHeight"]

        coretexAnnotation = CoretexImageAnnotation.create(imageName, width, height, [])

        for shape in imageAnnotation["shapes"]:
            instance = self.__extractInstance(shape)
            if instance is None:
                continue

            coretexAnnotation.instances.append(instance)

        self._saveImageAnnotationPair(os.path.join(self.__imagesPath, imageName), coretexAnnotation)

    def _extractSingleAnnotation(self, fileName: str) -> None:
        with open(fileName) as jsonFile:
            data = json.load(jsonFile)
            self.__extractImageAnnotation(data)
