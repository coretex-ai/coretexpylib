from typing import Type, Any, Optional

import logging

from ..dataset import *
from ..space import SpaceTask


def getDatasetType(task: SpaceTask, isLocal: bool) -> Type[Dataset]:
    if task == SpaceTask.other:
        if isLocal:
            return LocalCustomDataset

        return CustomDataset

    if task == SpaceTask.imageSegmentation:
        if isLocal:
            return LocalImageSegmentationDataset

        return ImageSegmentationDataset

    if task == SpaceTask.computerVision:
        if isLocal:
            return LocalComputerVisionDataset

        return ComputerVisionDataset

    logging.getLogger("coretexpylib").debug(f">> [Coretex] SpaceTask ({task}) does not have a dataset type using CustomDataset")

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