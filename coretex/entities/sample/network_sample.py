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

from typing import Any, TypeVar, Optional, Generic, Dict, Union
from typing_extensions import Self
from datetime import datetime
from pathlib import Path

import os
import time

from .sample import Sample
from ..project import ProjectType
from ... import folder_manager
from ...codable import KeyDescriptor
from ...networking import NetworkObject, networkManager, FileData, NetworkRequestError
from ...utils import TIME_ZONE
from ...cryptography import getProjectKey, aes


SampleDataType = TypeVar("SampleDataType")


class NetworkSample(Generic[SampleDataType], Sample[SampleDataType], NetworkObject):

    """
        Represents a base class for all Sample classes which are
        comunicating with Coretex.ai
    """

    isLocked: bool
    projectId: int
    projectType: ProjectType
    lastModified: datetime
    isEncrypted: bool

    @property
    def path(self) -> Path:
        """
            Returns
            -------
            Path -> path for network sample
        """

        return folder_manager.samplesFolder / str(self.id)

    @property
    def zipPath(self) -> Path:
        """
            Returns
            -------
            Path -> zip path for network sample
        """

        return self.path.with_suffix(".zip")

    @property
    def downloadPath(self) -> Path:
        """
            Returns
            -------
            Path -> path to which the network sample is downloaded to
        """

        return self.path.with_suffix(".bin") if self.isEncrypted else self.zipPath

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["projectType"] = KeyDescriptor("project_task", ProjectType)
        descriptors["lastModified"] = KeyDescriptor("storage_last_modified", datetime)

        return descriptors

    @classmethod
    def _endpoint(cls) -> str:
        return "session"

    @classmethod
    def _createSample(
        cls,
        parameters: Dict[str, Any],
        filePath: Union[Path, str],
        mimeType: Optional[str] = None
    ) -> Optional[Self]:
        """
            Uploads sample to Coretex.ai

            Parametrs
            ---------
            endpoint : str
                API endpoint
            parameters : Dict[str, Any]
                parameters which will be sent as request body
            filePath : Union[Path, str]
                path to sample
            mimeType : Optional[str]
                mimeType (not required)

            Returns
            -------
            Optional[Self] -> created sample object if request
            was successful, None otherwise
        """

        if isinstance(filePath, str):
            filePath = Path(filePath)

        files = [
            FileData.createFromPath("file", filePath, mimeType = mimeType)
        ]

        response = networkManager.formData("session/import", parameters, files)
        if response.hasFailed():
            return None

        return cls.decode(response.getJson(dict))

    def modifiedSinceLastDownload(self) -> bool:
        """
            Checking if sample has been modified since last download, if the sample is already
            stored locally

            Returns
            -------
            bool -> False if sample has not changed since last download, True otherwise

            Raises
            ------
            FileNotFoundError -> sample file cannot be found
        """

        if not self.downloadPath.exists():
            raise FileNotFoundError(
                f">> [Coretex] Sample file could not be found at {self.downloadPath}. "
                "Cannot check if file has been modified since last download"
            )

        lastModified = datetime.fromtimestamp(self.downloadPath.stat().st_mtime).astimezone(TIME_ZONE)
        return self.lastModified > lastModified

    def decrypt(self, ignoreCache: bool = False) -> None:
        """
            Decrypts the content of this Sample and caches
            the results. Is ignored if the "isEncrypted" value is False.

            Parameters
            ----------
            ignoreCache : bool
                defines if content should be decrypted if a cache for decryption
                already exists
        """

        if not self.isEncrypted:
            return

        if ignoreCache and self.zipPath.exists():
            self.zipPath.unlink()

        if not ignoreCache and self.zipPath.exists():
            return

        aes.decryptFile(getProjectKey(self.projectId), self.downloadPath, self.zipPath)

    def _relinkSample(self) -> None:
        for datasetPath in folder_manager.datasetsFolder.iterdir():
            sampleHardLinkPath = datasetPath / self.zipPath.name
            if not sampleHardLinkPath.exists():
                continue

            sampleHardLinkPath.unlink()
            os.link(self.zipPath, sampleHardLinkPath)

    def download(self, decrypt: bool = False, ignoreCache: bool = False) -> None:
        """
            Downloads sample from Coretex.ai

            Raises
            ------
            NetworkRequestError -> if some kind of error happened during
            the download process
        """

        if self.downloadPath.exists() and self.modifiedSinceLastDownload():
            ignoreCache = True

        if ignoreCache and self.downloadPath.exists():
            self.downloadPath.unlink()

        if not ignoreCache and self.downloadPath.exists():
            return

        if decrypt and not self.isEncrypted:
            # Change to false if sample is not encrypted
            decrypt = False

        params = {
            "id": self.id
        }

        response = networkManager.streamDownload(
            f"{self._endpoint()}/export",
            self.downloadPath,
            params
        )

        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to download Sample \"{self.name}\"")

        if decrypt:
            self.decrypt(ignoreCache)

        # Update sample download time to now
        os.utime(self.downloadPath, (os.stat(self.downloadPath).st_atime, time.time()))

        # If sample was downloaded succesfully relink it to datasets to which it is linked
        self._relinkSample()

    def load(self) -> SampleDataType:
        return super().load()  # type: ignore
