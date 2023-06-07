from typing import Tuple, TypeVar, Type, Optional
from pathlib import Path
from zipfile import ZipFile

import time
import json
import shutil
import zipfile

from coretex import *


RemoteDatasetType = TypeVar("RemoteDatasetType", bound = NetworkDataset)
LocalDatasetType = TypeVar("LocalDatasetType", bound = LocalDataset)


def generateUniqueName() -> str:
    return f"PythonUnitTests - {time.time()}"


def getDatasetPathForTask(task: SpaceTask) -> Path:
    resourcesPath = Path("./tests/resources")

    if task == SpaceTask.other:
        return resourcesPath / "other_dataset"

    if task == SpaceTask.computerVision:
        return resourcesPath / "computer_vision_dataset"

    raise ValueError(f">> [Coretex] {task.name} has no resources")


def _createSampleFor(task: SpaceTask, datasetId: int, samplePath: Path) -> Optional[NetworkSample]:
    if task == SpaceTask.other:
        return CustomSample.createCustomSample(generateUniqueName(), datasetId, samplePath)

    if task == SpaceTask.computerVision:
        extractionDir = samplePath.parent / samplePath.stem

        with ZipFile(samplePath) as zipFile:
            zipFile.extractall(extractionDir)

        sample = ImageSample.createImageSample(datasetId, extractionDir / "image.jpeg")

        shutil.rmtree(extractionDir)
        return sample

    raise ValueError(f">> [Coretex] Unsupported task {task.name}")


def createRemoteEnvironmentFor(task: SpaceTask, datasetType: Type[RemoteDatasetType]) -> Tuple[Space, RemoteDatasetType]:
    space = Space.createSpace(generateUniqueName(), task)
    if space is None:
        raise ValueError(">> [Coretex] Failed to create space")

    dataset = datasetType.createDataset(generateUniqueName(), space.id)
    if dataset is None:
        raise ValueError(">> [Coretex] Failed to create dataset")

    datasetPath = getDatasetPathForTask(task)
    for path in datasetPath.iterdir():
        # Gotta check this because macos creates .DS_store files
        if not zipfile.is_zipfile(path):
            continue

        sample = _createSampleFor(task, dataset.id, path)
        if sample is None:
            raise ValueError(">> [Coretex] Failed to create sample")

    if isinstance(dataset, ComputerVisionDataset):
        with datasetPath.joinpath("classes.json").open("r") as classFile:
            classes = ImageDatasetClasses(
                [ImageDatasetClass.decode(element) for element in json.load(classFile)]
            )

            if not dataset.saveClasses(classes):
                raise RuntimeError(">> [Coretex] Failed to create classes for ComputerVision dataset")

    if not dataset.refresh():
        raise RuntimeError(">> [Coretex] Failed to fetch dataset")

    return space, dataset  # type: ignore


def createLocalEnvironmentFor(task: SpaceTask, datasetType: Type[LocalDatasetType]) -> LocalDatasetType:
    return datasetType(getDatasetPathForTask(task))  # type: ignore
