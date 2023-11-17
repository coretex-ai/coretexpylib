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

import os
import glob
import xml.etree.ElementTree as ET

from .shared import getTag, toInt
from .instance_extractor import InstanceExtractor
from ...base_converter import BaseConverter
from .....entities import CoretexImageAnnotation


class PascalSegConverter(BaseConverter):

    """
        Represents the Converter from Pascal VOC 2012 Format to Cortex Format
    """

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        super().__init__(datasetName, projectId, datasetPath)

        self.__imagesPath = os.path.join(datasetPath, "JPEGImages")
        self.__segmentationPath = os.path.join(datasetPath, "SegmentationObject")

        annotations = os.path.join(datasetPath, "Annotations")
        self.__fileNames = glob.glob(os.path.join(annotations, "*.xml"))

    def _dataSource(self) -> List[str]:
        return self.__fileNames

    def _extractLabels(self) -> Set[str]:
        labels: Set[str] = set()

        for filename in self.__fileNames:
            tree = ET.parse(filename)
            root = tree.getroot()
            objects = root.findall("object")

            for obj in objects:
                labelElement = obj.find("name")
                if labelElement is None:
                    continue

                label = labelElement.text
                if label is None:
                    continue

                labels.add(label)

        return labels

    def __extractImageAnnotation(self, root: ET.Element) -> None:
        fileName = getTag(root, "filename")
        if fileName is None:
            return

        baseFileName = os.path.splitext(fileName)[0]
        filenamePNG = f"{baseFileName}.png"

        if not os.path.exists(os.path.join(self.__imagesPath, fileName)):
            return

        instanceExtractor = InstanceExtractor(self._dataset)
        instances = instanceExtractor.extractInstances(root, filenamePNG, self.__segmentationPath)

        size = root.find('size')
        if size is None:
            return

        width, height = toInt(size, "width", "height")
        if width is None or height is None:
            return

        coretexAnnotation = CoretexImageAnnotation.create(fileName, width, height, instances)
        self._saveImageAnnotationPair(os.path.join(self.__imagesPath, fileName), coretexAnnotation)

    def _extractSingleAnnotation(self, fileName: str) -> None:
        tree = ET.parse(fileName)
        root = tree.getroot()

        self.__extractImageAnnotation(root)
