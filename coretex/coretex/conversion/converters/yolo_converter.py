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
import re
import logging

from PIL import Image

from ..base_converter import BaseConverter
from ...annotation import CoretexImageAnnotation, CoretexSegmentationInstance, BBox


class Helper:

    @staticmethod
    def isFloat(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False


class YoloConverter(BaseConverter):

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        super().__init__(datasetName, projectId, datasetPath)

        self.__imagesPath = os.path.join(datasetPath, "images")
        self.__annotations = os.path.join(datasetPath, "annotations")

        classesPath = os.path.join(self.__annotations, "classes.txt")
        if not os.path.exists(classesPath):
            raise FileNotFoundError(">> [Coretex] classes.txt file not found")

        with open(classesPath, 'r') as f:
            text = f.read()
            self.__rawLabels = text.split("\n")
            self.__rawLabels = [label for label in self.__rawLabels if label]

    def _dataSource(self) -> List[str]:
        return os.listdir(self.__annotations)

    def _extractLabels(self) -> Set[str]:
        return set(self.__rawLabels)

    def __extractBBox(self, rawInstance: List[str], width: int, height: int) -> BBox:
        xYolo = float(rawInstance[1])
        yYolo = float(rawInstance[2])
        wYolo = float(rawInstance[3])
        hYolo = float(rawInstance[4])

        boxWidth = int(wYolo * width)
        boxHeight = int(hYolo * height)
        xMin = int(xYolo * width - (boxWidth / 2))
        yMin = int(yYolo * height - (boxHeight / 2))

        return BBox(xMin, yMin, boxWidth, boxHeight)

    def __extractInstance(self, rawInstance: List[str], width: int, height: int) -> Optional[CoretexSegmentationInstance]:
        # Get class name
        labelId = int(rawInstance[0])
        label = self.__rawLabels[labelId]

        coretexClass = self._dataset.classByName(label)
        if coretexClass is None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] Class: ({label}) is not a part of dataset")
            return None

        bbox = self.__extractBBox(rawInstance, width, height)
        return CoretexSegmentationInstance.create( coretexClass.classIds[0], bbox, [bbox.polygon])

    def _extractSingleAnnotation(self, yoloFilePath: str) -> None:
        if not yoloFilePath.endswith("txt"):
            return

        if os.path.splitext(yoloFilePath)[0] == "classes":
            return

        yoloFilePath = os.path.join(self.__annotations, yoloFilePath)
        yoloName = os.path.basename(yoloFilePath)

        imagePath = self.imageCheck(os.path.join(self.__imagesPath, yoloName))
        if imagePath is not None:
            imageName = os.path.basename(imagePath)

        baseImageName = os.path.splitext(imageName)[0]
        baseYoloName = os.path.splitext(yoloName)[0]

        if baseImageName != baseYoloName:
            return

        with open(yoloFilePath, 'r') as file:
            allLines = file.readlines()

            image = Image.open(imagePath)
            coretexAnnotation = CoretexImageAnnotation.create(imageName, image.width, image.height, [])

            # Get bounding boxes and classes from yolo txt
            for line in allLines:
                yoloArray = re.split("\s", line.rstrip())
                isFormatCorrect = YoloConverter.formatCheck(yoloArray)

                if not isFormatCorrect:
                    continue

                instance = self.__extractInstance(yoloArray, image.width, image.height)
                if instance is None:
                    continue

                coretexAnnotation.instances.append(instance)

            self._saveImageAnnotationPair(os.path.join(self.__imagesPath, imageName), coretexAnnotation)

    @staticmethod
    def imageCheck(yoloFilePath: str) -> Optional[str]:
        if os.path.exists(yoloFilePath.replace('txt', 'jpeg')):
            return yoloFilePath.replace('txt', 'jpeg')
        if os.path.exists(yoloFilePath.replace('txt', 'jpg')):
            return yoloFilePath.replace('txt', 'jpg')
        if os.path.exists(yoloFilePath.replace('txt', 'png')):
           return yoloFilePath.replace('txt', 'png')

        return None

    @staticmethod
    def formatCheck(yoloArray: List[str]) -> bool:
        """
            Checks format of yolo annotation file

            Parameters
            ----------
            yoloArray : List[str]
                list with label id and bounding boxes

            Returns
            -------
            bool -> True if format is correct, False if format is not correct
        """

        if len(yoloArray) != 5:
            return False

        for value in yoloArray:
            if not Helper.isFloat(value):
                return False

        return True
