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

from typing import Optional, List, Set

import os
import logging
import glob
import xml.etree.ElementTree as ET

from .pascal.shared import getTag, getBoxes, toInt
from ..base_converter import BaseConverter
from ...annotation import CoretexImageAnnotation, CoretexSegmentationInstance, BBox


class VOCConverter(BaseConverter):

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        super().__init__(datasetName, projectId, datasetPath)

        self.__imagesPath = os.path.join(datasetPath, "images")

        annotations = os.path.join(datasetPath, "annotations")
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

    def __extractInstance(self, obj: ET.Element) -> Optional[CoretexSegmentationInstance]:
        label = getTag(obj, "name")
        if label is None:
            return None

        coretexClass = self._dataset.classByName(label)
        if coretexClass is None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] Class: ({label}) is not a part of dataset")
            return None

        bboxElement = obj.find('bndbox')
        if bboxElement is None:
            return None

        encodedBbox = getBoxes(bboxElement)
        if encodedBbox is None:
            return None

        bbox = BBox.decode(encodedBbox)
        return CoretexSegmentationInstance.create(coretexClass.classIds[0], bbox, [bbox.polygon])

    def _extractImageAnnotation(self, root: ET.Element) -> None:
        fileName = getTag(root, "filename")
        if fileName is None:
            return

        size = root.find('size')
        if size is None:
            return

        width, height = toInt(size, "width", "height")
        if width is None or height is None:
            return

        coretexAnnotation = CoretexImageAnnotation.create(fileName, width, height, [])

        for obj in root.findall("object"):
            instance = self.__extractInstance(obj)
            if instance is None:
                continue

            coretexAnnotation.instances.append(instance)

        self._saveImageAnnotationPair(os.path.join(self.__imagesPath, fileName), coretexAnnotation)

    def _extractSingleAnnotation(self, fileName: str) -> None:
        tree = ET.parse(fileName)
        root = tree.getroot()

        self._extractImageAnnotation(root)
