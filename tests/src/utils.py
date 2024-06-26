from typing import Tuple, TypeVar, Type
from pathlib import Path
from zipfile import ZipFile

import time
import json
import shutil
import zipfile

from coretex import NetworkDataset, LocalDataset, ProjectType, NetworkSample, Project, \
    ImageDataset, ImageDatasetClasses, ImageDatasetClass, createDataset


RemoteDatasetType = TypeVar("RemoteDatasetType", bound = NetworkDataset)
LocalDatasetType = TypeVar("LocalDatasetType", bound = LocalDataset)


def generateUniqueName() -> str:
    return f"python-unit-test-{int(time.time())}"


def getDatasetPathForType(type_: ProjectType) -> Path:
    resourcesPath = Path("./tests/resources")

    if type_ == ProjectType.other:
        return resourcesPath / "other_dataset"

    if type_ == ProjectType.computerVision:
        return resourcesPath / "computer_vision_dataset"

    raise ValueError(f">> [Coretex] {type_.name} has no resources")


def _createSampleFor(type_: ProjectType, dataset: NetworkDataset[NetworkSample], samplePath: Path) -> NetworkSample:
    if type_ == ProjectType.other:
        return dataset.add(samplePath, generateUniqueName())

    if type_ == ProjectType.computerVision:
        extractionDir = samplePath.parent / samplePath.stem

        with ZipFile(samplePath) as zipFile:
            zipFile.extractall(extractionDir)

        sample = dataset.add(extractionDir / "image.jpeg")

        shutil.rmtree(extractionDir)
        return sample

    raise ValueError(f">> [Coretex] Unsupported type {type_.name}")


def createRemoteEnvironmentFor(type_: ProjectType, datasetType: Type[RemoteDatasetType]) -> Tuple[Project, RemoteDatasetType]:
    project = Project.createProject(generateUniqueName(), type_)
    if project is None:
        raise ValueError(">> [Coretex] Failed to create project")

    with createDataset(datasetType, generateUniqueName(), project.id) as dataset:
        datasetPath = getDatasetPathForType(type_)
        for path in datasetPath.iterdir():
            # Gotta check this because macos creates .DS_store files
            if not zipfile.is_zipfile(path):
                continue

            sample = _createSampleFor(type_, dataset, path)
            if sample is None:
                raise ValueError(">> [Coretex] Failed to create sample")

        if isinstance(dataset, ImageDataset):
            with datasetPath.joinpath("classes.json").open("r") as classFile:
                classes = ImageDatasetClasses(
                    [ImageDatasetClass.decode(element) for element in json.load(classFile)]
                )

                if not dataset.saveClasses(classes):
                    raise RuntimeError(">> [Coretex] Failed to create classes for ComputerVision dataset")

    if not dataset.refresh():
        raise RuntimeError(">> [Coretex] Failed to fetch dataset")

    return project, dataset


def createLocalEnvironmentFor(type_: ProjectType, datasetType: Type[LocalDatasetType]) -> LocalDatasetType:
    return datasetType(getDatasetPathForType(type_))  # type: ignore
