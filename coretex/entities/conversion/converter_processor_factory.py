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

from typing import Final

from .base_converter import ConverterProcessorType, BaseConverter
from .converters import *


class ConverterProcessorFactory:
    """
        Factory class used to create different types
        of BaseConverter objects based on the convertProcessorType
        property of the class

        Properties
        ----------
        convertProcessorType : ConverterProcessorType
            type of converter for convertin dataset
    """

    def __init__(self, convertProcessorType: ConverterProcessorType):
        self.type: Final = convertProcessorType

    def create(self, datasetName: str, projectId: int, datasetPath: str) -> BaseConverter:
        """
            Creates BaseConverter based on the convertProcessorType
            property of the class

            Parameters
            ----------
            datasetName : str
                name of dataset
            projectId : int
                id of Coretex Project
            datasetPath : str
                path to dataset

            Returns
            -------
            Appropriate BaseConverter object based on
            convertProcessorType
        """

        if self.type == ConverterProcessorType.coco:
            return COCOConverter(datasetName, projectId, datasetPath)

        if self.type == ConverterProcessorType.yolo:
            return YoloConverter(datasetName, projectId, datasetPath)

        if self.type ==  ConverterProcessorType.createML:
            return CreateMLConverter(datasetName, projectId, datasetPath)

        if self.type == ConverterProcessorType.voc:
            return VOCConverter(datasetName, projectId, datasetPath)

        if self.type == ConverterProcessorType.labelMe:
            return LabelMeConverter(datasetName, projectId, datasetPath)

        if self.type == ConverterProcessorType.pascalSeg:
            return PascalSegConverter(datasetName, projectId, datasetPath)

        if self.type == ConverterProcessorType.humanSegmentation:
            return HumanSegmentationConverter(datasetName, projectId, datasetPath)

        if self.type == ConverterProcessorType.cityScape:
            return CityScapeConverter(datasetName, projectId, datasetPath)

        raise RuntimeError()
