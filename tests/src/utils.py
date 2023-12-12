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


def getDatasetPathForType(type_: ProjectType) -> Path:
    resourcesPath = Path("./tests/resources")

    if type_ == ProjectType.other:
        return resourcesPath / "other_dataset"

    if type_ == ProjectType.computerVision:
        return resourcesPath / "computer_vision_dataset"

    raise ValueError(f">> [Coretex] {type_.name} has no resources")


def _createSampleFor(type_: ProjectType, datasetId: int, samplePath: Path) -> Optional[NetworkSample]:
    if type_ == ProjectType.other:
        return CustomSample.createCustomSample(generateUniqueName(), datasetId, samplePath)

    if type_ == ProjectType.computerVision:
        extractionDir = samplePath.parent / samplePath.stem

        with ZipFile(samplePath) as zipFile:
            zipFile.extractall(extractionDir)

        sample = ImageSample.createImageSample(datasetId, extractionDir / "image.jpeg")

        shutil.rmtree(extractionDir)
        return sample

    raise ValueError(f">> [Coretex] Unsupported type {type_.name}")


def createRemoteEnvironmentFor(Type_: ProjectType, datasetType: Type[RemoteDatasetType]) -> Tuple[Project, RemoteDatasetType]:
    project = Project.createProject(generateUniqueName(), Type_)
    if project is None:
        raise ValueError(">> [Coretex] Failed to create project")

    with createDataset(datasetType, generateUniqueName(), project.id) as dataset:
        datasetPath = getDatasetPathForType(Type_)
        for path in datasetPath.iterdir():
            # Gotta check this because macos creates .DS_store files
            if not zipfile.is_zipfile(path):
                continue

            sample = _createSampleFor(Type_, dataset.id, path)
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

    return project, dataset  # type: ignore


def createLocalEnvironmentFor(Type_: ProjectType, datasetType: Type[LocalDatasetType]) -> LocalDatasetType:
    return datasetType(getDatasetPathForType(Type_))  # type: ignore
