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

from typing import Any, Final, Optional, List, Set
from enum import Enum
from abc import ABC, abstractmethod

import logging

from ..annotation import CoretexImageAnnotation
from ...entities import ImageDataset, ImageSample, ImageDatasetClass
from ...threading import MultithreadedDataProcessor


ImageDatasetType = ImageDataset[ImageSample]


class ConverterProcessorType(Enum):

    """
        List of all annotation formats supported by Coretex
    """

    coco = 0
    yolo = 1
    createML = 2
    voc = 3
    labelMe = 4
    pascalSeg = 5

    # TODO: Migrate to Human Segmentation task template repo, or try to make it generic
    humanSegmentation = 6

    cityScape = 7


class BaseConverter(ABC):

    """
        Base class for Coretex Annotation format conversion

        Properties
        ----------
        datasetName : str
            name of dataset
        projectId : int
            id of Coretex Project
        datasetPath : str
            path to dataset
    """

    def __init__(self, datasetName: str, projectId: int, datasetPath: str) -> None:
        dataset: ImageDatasetType = ImageDataset.createDataset(datasetName, projectId)

        self._dataset: Final = dataset
        self._datasetPath: Final = datasetPath

    def _saveImageAnnotationPair(self, imagePath: str, annotation: CoretexImageAnnotation) -> None:
        # Create sample
        sample = ImageSample.createImageSample(self._dataset.id, imagePath)
        if sample is None:
            logging.getLogger("coretexpylib").info(">> [Coretex] Failed to create sample")
            return

        # Add created sample to dataset
        self._dataset.samples.append(sample)

        # Attach annotation to sample
        if not sample.saveAnnotation(annotation):
            logging.getLogger("coretexpylib").info(">> [Coretex] Failed to save ImageSample annotation")

    @abstractmethod
    def _dataSource(self) -> List[Any]:
        pass

    @abstractmethod
    def _extractLabels(self) -> Set[str]:
        pass

    @abstractmethod
    def _extractSingleAnnotation(self, value: Any) -> None:
        pass

    def convert(self) -> ImageDatasetType:
        """
            Converts the dataset to Coretex Format

            Returns
            -------
            ImageDatasetType -> The converted ImageDataset object
        """

        # Extract classes
        labels = self._extractLabels()
        classes = ImageDatasetClass.generate(labels)

        if self._dataset.saveClasses(classes):
            logging.getLogger("coretexpylib").info(">> [Coretex] Dataset classes saved successfully")
        else:
            logging.getLogger("coretexpylib").info(">> [Coretex] Failed to save dataset classes")

        # Extract annotations
        MultithreadedDataProcessor(
            self._dataSource(),
            self._extractSingleAnnotation,
            message = "Converting dataset..."
        ).process()

        if not self._dataset.finalize():
            raise ValueError(f"Failed to finalize dataset \"{self._dataset.name}\"")

        return self._dataset
