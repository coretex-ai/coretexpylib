from typing import Type, Any, Optional

import logging

from ..dataset import *
from ..project import ProjectType


def getDatasetType(type_: ProjectType, isLocal: bool) -> Type[Dataset]:
    if type_ == ProjectType.other:
        if isLocal:
            return LocalCustomDataset

        return CustomDataset

    if type_ == ProjectType.imageSegmentation:
        if isLocal:
            return LocalImageSegmentationDataset

        return ImageSegmentationDataset

    if type_ == ProjectType.computerVision:
        if isLocal:
            return LocalComputerVisionDataset

        return ComputerVisionDataset

    logging.getLogger("coretexpylib").debug(f">> [Coretex] ProjectType ({type_}) does not have a dataset type using CustomDataset")

    # Returning CustomDataset in case the type_ doesn't have it's dataset type
    if isLocal:
        return LocalCustomDataset

    return CustomDataset


def fetchDataset(datasetType: Type[Dataset], value: Any) -> Optional[Dataset]:
    if issubclass(datasetType, LocalDataset):
        return datasetType(value)  # type: ignore

    if issubclass(datasetType, NetworkDataset):
        return datasetType.fetchById(value)

    return None