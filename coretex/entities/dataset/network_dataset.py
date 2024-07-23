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

from typing import Optional, TypeVar, Generic, List, Dict, Any, Type, Union
from typing_extensions import Self
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from contextlib import ExitStack

import hashlib
import base64
import logging

from .dataset import Dataset
from .state import DatasetState
from ..sample import NetworkSample
from ..utils import isEntityNameValid
from ... import folder_manager
from ...codable import KeyDescriptor
from ...networking import NetworkObject, \
    fileChunkUpload, networkManager, NetworkRequestError
from ...threading import MultithreadedDataProcessor
from ...cryptography import aes, getProjectKey
from ...utils.file import isArchive, archive


SampleType = TypeVar("SampleType", bound = "NetworkSample")
NAME_VALIDATION_MESSAGE = ">> [Coretex] Entity name is invalid. Requirements: alphanumeric characters (\"a-z\", and \"0-9\") and dash (\"-\") with length between 3 to 50"
MAX_DATASET_NAME_LENGTH = 50


def _hashDependencies(dependencies: List[str]) -> str:
    hash = hashlib.md5()
    hash.update("".join(sorted(dependencies)).encode())

    hashString = base64.b64encode(hash.digest()).decode("ascii")
    hashString = hashString.lower()
    hashString = hashString.replace("+", "0")
    hashString = hashString.replace("/", "0")
    hashString = hashString.replace("=", "0")

    return hashString


def _chunkSampleImport(sampleType: Type[SampleType], sampleName: str, samplePath: Path, datasetId: int) -> SampleType:
    parameters = {
        "name": sampleName,
        "dataset_id": datasetId,
        "file_id": fileChunkUpload(samplePath)
    }

    response = networkManager.formData("session/import", parameters, timeout = (5, 300))
    if response.hasFailed():
        raise NetworkRequestError(response, f"Failed to create sample from \"{samplePath}\"")

    return sampleType.decode(response.getJson(dict))


def _encryptedSampleImport(sampleType: Type[SampleType], sampleName: str, samplePath: Path, datasetId: int, key: bytes) -> SampleType:
    with ExitStack() as stack:
        if isArchive(samplePath):
            archivePath = samplePath
        else:
            archivePath = stack.enter_context(folder_manager.tempFile())
            archive(samplePath, archivePath)

        encryptedPath = stack.enter_context(folder_manager.tempFile())
        aes.encryptFile(key, archivePath, encryptedPath)

        return _chunkSampleImport(sampleType, sampleName, encryptedPath, datasetId)

    # ExitStack is marked as something that can "swallow" exceptions raised
    # in "with" block. In this case ExitStack does not enter any context
    # which can swallow the exceptions so this is not reachable, but mypy
    # is complaning about this and we silence it by raising an exception here
    raise RuntimeError("Unreachable statement was reached.")


class NetworkDataset(Generic[SampleType], Dataset[SampleType], NetworkObject, ABC):

    """
        Represents the base class for all Dataset classes which are
        comunicating with Coretex.ai

        Properties
        ----------
        createdOn : datetime
            creation date of dataset
        createdById : str
            id of created dataset id
        isLocked : bool
            availabilty of dataset for modifications
    """

    projectId: int
    createdOn: datetime
    createdById: str
    isLocked: bool
    isEncrypted: bool
    meta: Optional[Dict[str, Any]]

    def __init__(self, sampleType: Type[SampleType]) -> None:
        self._sampleType = sampleType

    @property
    def path(self) -> Path:
        """
            Retrieves path of dataset

            Returns
            -------
            Path -> path of dataset
        """

        return folder_manager.datasetsFolder / str(self.id)

    # Codable overrides

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["projectId"] = KeyDescriptor("project_id")
        descriptors["samples"] = KeyDescriptor("sessions", NetworkSample, list)

        return descriptors

    # NetworkObject overrides

    @classmethod
    def _endpoint(cls) -> str:
        return "dataset"

    @classmethod
    def fetchById(cls, objectId: int, **kwargs: Any) -> Self:
        if "include_sessions" not in kwargs:
            kwargs["include_sessions"] = 1

        return super().fetchById(objectId, **kwargs)

    @classmethod
    def fetchAll(cls, **kwargs: Any) -> List[Self]:
        if "include_sessions" not in kwargs:
            kwargs["include_sessions"] = 1

        return super().fetchAll(**kwargs)

    @classmethod
    def fetchCachedDataset(cls, dependencies: List[str]) -> Self:
        """
            Fetches cached dataset if it exists

            Parameters
            ----------
            dependencies : List[str]
                Parameters on which the cached dataset depends

            Returns
            -------
            Self -> Fetched dataset object

            Raises
            ------
            ValueError -> If dataset doesn't exist
        """

        return super().fetchOne(
            name = _hashDependencies(dependencies),
            include_sessions = 1
        )

    # Dataset methods

    @classmethod
    def createDataset(
        cls,
        name: str,
        projectId: int,
        meta: Optional[Dict[str, Any]] = None
    ) -> Self:

        """
            Creates a new dataset with the provided name and type

            Parameters
            ----------
            name : str
                dataset name
            projectId : int
                project for which the dataset will be created

            Returns
            -------
            The created dataset object or None if creation failed

            Raises
            ------
            ValueError -> If name is invalid
            NetworkRequestError -> If dataset creation failed

            Example
            -------
            >>> from coretex import NetworkDataset
            \b
            >>> dummyDataset = NetworkDataset.createDataset("dummyDataset", 123)
        """

        if not isEntityNameValid(name):
            raise ValueError(NAME_VALIDATION_MESSAGE)

        return cls.create(
            name = name,
            project_id = projectId,
            meta = meta
        )

    @classmethod
    def generateCacheName(cls, prefix: str, dependencies: List[str]) -> str:
        """
            Generated dataset name based on the dependencies

            Parameters
            ----------
            prefix : str
                prefix to which the dependency hash will be appended
            dependencies : List[str]
                parameters which affect the contents of the cache

            Returns
            -------
            str -> prefix with hash generated based on dependencies appended
        """

        if MAX_DATASET_NAME_LENGTH - len(prefix) < 8:
            raise ValueError(f"Dataset prefix \"{prefix}\" is too long. Max allowed size is \"{MAX_DATASET_NAME_LENGTH - 8}\".")

        suffix = _hashDependencies(dependencies)
        name = f"{prefix}-{suffix}"

        if len(name) > MAX_DATASET_NAME_LENGTH:
            name = name[:MAX_DATASET_NAME_LENGTH]

        return name

    @classmethod
    def createCacheDataset(cls, prefix: str, dependencies: List[str], projectId: int) -> Self:
        """
            Creates a dataset used for caching results of tasks
            Used to avoid repeating expensive and long calculations

            Parameters
            ----------
            prefix : str
                prefix of the cache dataset
            dependencies : List[str]
                parameters which affect the contents of the cache
            projectId : int
                project for which the dataset will be created
        """

        if not isEntityNameValid(prefix):
            raise ValueError(NAME_VALIDATION_MESSAGE)

        dataset = cls.createDataset(cls.generateCacheName(prefix, dependencies), projectId)
        if dataset is None:
            raise ValueError(f"Failed to create cache dataset with prefix \"{prefix}\"")

        return dataset

    def finalize(self) -> bool:
        """
            Finalizes state of Coretex dataset

            Example
            -------
            >>> from coretex import CustomDataset
            \b
            >>> dummyDataset = CustomDataset.createDataset("dummyDataset", 123)
            >>> dummyDataset.finalize()
        """

        return self.update(name = self.name, state = DatasetState.final)

    def _linkSamplePath(self, samplePath: Path) -> None:
        linkPath = self.path / samplePath.name
        if linkPath.exists():
            linkPath.unlink()

        samplePath.link_to(linkPath)

    def download(self, decrypt: bool = True, ignoreCache: bool = False) -> None:
        """
            Downloads dataset from Coretex

            Parameters
            ----------
            ignoreCache : bool
                if dataset is already downloaded and ignoreCache
                is True it will be downloaded again (not required)

            Example
            -------
            >>> from coretex import NetworkDataset
            \b
            >>> dummyDataset = NetworkDataset.fetchById(1023)
            >>> dummyDataset.download()
        """

        self.path.mkdir(exist_ok = True)

        def sampleDownloader(sample: SampleType) -> None:
            sample.download(decrypt, ignoreCache)

            if sample.downloadPath.exists():
                self._linkSamplePath(sample.downloadPath)

            if sample.zipPath.exists():
                self._linkSamplePath(sample.zipPath)

            logging.getLogger("coretexpylib").info(f"\tDownloaded \"{sample.name}\"")

        processor = MultithreadedDataProcessor(
            self.samples,
            sampleDownloader,
            message = f"Downloading dataset \"{self.name}\"..."
        )

        processor.process()

    def rename(self, name: str) -> bool:
        if not isEntityNameValid(name):
            raise ValueError(NAME_VALIDATION_MESSAGE)

        success = self.update(name = name)

        if success:
            return super().rename(name)

        return success

    @abstractmethod
    def _uploadSample(self, samplePath: Path, sampleName: str, **metadata: Any) -> SampleType:
        # Override in data specific classes (ImageDataset, SequenceDataset, etc...)
        # to implement a specific way of uploading samples
        pass

    def add(self, samplePath: Union[Path, str], sampleName: Optional[str] = None, **metadata: Any) -> SampleType:
        """
            Uploads the provided archive (.zip, .tar.gz) as Sample to
            Coretex.ai as a part of this Dataset.

            Parametrs
            ---------
            path : Union[Path, str]
                path to data which will be uploaded

            Returns
            -------
            SampleType -> created Sample
        """

        if isinstance(samplePath, str):
            samplePath = Path(samplePath)

        if sampleName is None:
            sampleName = samplePath.stem

        if self.isEncrypted:
            sample = _encryptedSampleImport(self._sampleType, sampleName, samplePath, self.id, getProjectKey(self.projectId))
        else:
            sample = self._uploadSample(samplePath, sampleName, **metadata)

        # Append the newly created sample to the list of samples
        self.samples.append(sample)

        return sample
