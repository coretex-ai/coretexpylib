from typing import Type, Any, Optional

import logging

from ..dataset import *
from ..project import ProjectType


def getDatasetType(task: ProjectType, isLocal: bool) -> Type[Dataset]:
    if task == ProjectType.other:
        if isLocal:
            return LocalCustomDataset

        return CustomDataset

    if task == ProjectType.imageSegmentation:
        if isLocal:
            return LocalImageSegmentationDataset

        return ImageSegmentationDataset

    if task == ProjectType.computerVision:
        if isLocal:
            return LocalComputerVisionDataset

        return ComputerVisionDataset

    logging.getLogger("coretexpylib").debug(f">> [Coretex] ProjectType ({task}) does not have a dataset type using CustomDataset")

    # Returning CustomDataset in case the task doesn't have it's dataset type
    if isLocal:
        return LocalCustomDataset

    return CustomDataset


def fetchDataset(datasetType: Type[Dataset], value: Any) -> Optional[Dataset]:
    if issubclass(datasetType, LocalDataset):
        return datasetType(value)  # type: ignore

    if issubclass(datasetType, NetworkDataset):
        return datasetType.fetchById(value)

    return None