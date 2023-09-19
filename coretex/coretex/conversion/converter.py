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

from typing import Optional

from .converter_processor_factory import ConverterProcessorFactory
from .base_converter import ConverterProcessorType
from ..dataset import ImageDataset


def convert(type: ConverterProcessorType, datasetName: str, projectId: int, datasetPath: str) -> Optional[ImageDataset]:
    """
        Converts and uploads the given dataset to Coretex Format

        Parameters
        ----------
        type : ConverterProcessorType
            dataset format type (coco, yolo, createML, voc, labelMe, pascalSeg)
        datasetName : str
            name of dataset
        projectId : str
            id of Coretex Project
        datasetPath : str
            path to dataset

        Returns
        -------
        Optional[ImageDataset] -> The converted ImageDataset object

        Example
        -------
        >>> from coretex import convert, ConverterProcessorType
        \b
        >>> dataset = convert(
                type = ConvertProcessorType.coco,
                datasetName = "coretex_dataset",
                projectId = 1023,
                datasetPath = "path/to/dataset"
            )
        >>> if dataset is not None:
                print("Dataset converted successfully")
    """

    return ConverterProcessorFactory(type).create(datasetName, projectId, datasetPath).convert()
