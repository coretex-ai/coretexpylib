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

import os
import json
import glob
import logging

from PIL import Image

from ..base_converter import BaseConverter
from ...annotation import CoretexSegmentationInstance, CoretexImageAnnotation, BBox


class CreateMLConverter(BaseConverter):

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
                data = json.load(jsonFile)[0]

                for annotation in data["annotations"]:
                    labels.add(annotation["label"])

        return labels

    def __extractBBox(self, bbox: Dict[str, int]) -> BBox:
        return BBox(
            bbox["x"] - bbox["width"] // 2,
            bbox["y"] - bbox["height"] // 2,
            bbox["width"],
            bbox["height"]
        )

    def __extractInstance(self, annotation: Dict[str, Any]) -> Optional[CoretexSegmentationInstance]:
        label = annotation["label"]

        coretexClass = self._dataset.classByName(label)
        if coretexClass is None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] Class: ({label}) is not a part of dataset")
            return None

        bbox = self.__extractBBox(annotation["coordinates"])
        return CoretexSegmentationInstance.create(coretexClass.classIds[0], bbox, [bbox.polygon])

    def __extractImageAnnotation(self, imageAnnotation: Dict[str, Any]) -> None:
        imageName = imageAnnotation["image"]
        image = Image.open(f"{self.__imagesPath}/{imageName}")

        coretexAnnotation = CoretexImageAnnotation.create(imageName, image.width, image.height, [])

        for annotation in imageAnnotation["annotations"]:
            instance = self.__extractInstance(annotation)
            if instance is None:
                continue

            coretexAnnotation.instances.append(instance)

        self._saveImageAnnotationPair(os.path.join(self.__imagesPath, imageName), coretexAnnotation)

    def _extractSingleAnnotation(self, fileName: str) -> None:
        with open(fileName) as jsonFile:
            data = json.load(jsonFile)[0]

            self.__extractImageAnnotation(data)
