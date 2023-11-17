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

from typing import Optional, TypeVar, Generic, List, Dict, Any
from typing_extensions import Self
from datetime import datetime
from pathlib import Path

import hashlib
import base64
import logging

from .dataset import Dataset
from ..sample import NetworkSample
from ... import folder_manager
from ...codable import KeyDescriptor
from ...networking import NetworkObject
from ...threading import MultithreadedDataProcessor


SampleType = TypeVar("SampleType", bound = "NetworkSample")
MAX_DATASET_NAME_LENGTH = 50


class NetworkDataset(Generic[SampleType], Dataset[SampleType], NetworkObject):

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
    meta: Optional[Dict[str, Any]]

    def __init__(self) -> None:
        pass

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

    # Dataset methods

    @classmethod
    def createDataset(
        cls,
        name: str,
        projectId: int,
        meta: Optional[Dict[str, Any]] = None
    ) -> Optional[Self]:

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

            Example
            -------
            >>> from coretex import NetworkDataset
            \b
            >>> dummyDataset = NetworkDataset.createDataset("dummyDataset", 123)
            >>> if dummyDataset is not None:
                    print("Dataset created successfully")
        """

        return cls.create(
            name = name,
            project_id = projectId,
            meta = meta
        )

    @classmethod
    def generateCachedName(cls, name: str, dependencies: List[str]) -> str:
        if MAX_DATASET_NAME_LENGTH - len(name) < 8:
            raise ValueError(f"Dataset name \"{name}\" is too long. Max allowed size is \"{MAX_DATASET_NAME_LENGTH}\".")

        hash = hashlib.md5()
        hash.update("-".join(sorted(dependencies)).encode())
        suffix = base64.b64encode(hash.digest()).decode("ascii").replace("+", "0")

        name = f"{name} - {suffix}"
        if len(name) > MAX_DATASET_NAME_LENGTH:
            name = name[:MAX_DATASET_NAME_LENGTH]

        return name

    @classmethod
    def createCachedDataset(cls, name: str, spaceId: int, dependencies: List[str]) -> Optional[Self]:
        return cls.createDataset(cls.generateCachedName(name, dependencies), spaceId)

    def download(self, ignoreCache: bool = False) -> None:
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
            downloadSuccess = sample.download(ignoreCache)
            if not downloadSuccess:
                raise RuntimeError(f">> [Coretex] Failed to download sample \"{sample.name}\"")

            sampleHardLinkPath = self.path / sample.zipPath.name
            if not sampleHardLinkPath.exists():
                sample.zipPath.link_to(sampleHardLinkPath)

            logging.getLogger("coretexpylib").info(f"\tDownloaded \"{sample.name}\"")

        processor = MultithreadedDataProcessor(
            self.samples,
            sampleDownloader,
            message = f"Downloading dataset \"{self.name}\"..."
        )

        processor.process()

    def rename(self, name: str) -> bool:
        success = self.update(name = name)

        if success:
            return super().rename(name)

        return success
