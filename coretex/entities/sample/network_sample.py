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

from typing import TypeVar, Generic, Dict, Any, List
from typing_extensions import override
from datetime import datetime
from pathlib import Path

import os
import time
import shutil

from .sample import Sample
from ..project import ProjectType
from ... import folder_manager
from ...codable import KeyDescriptor
from ...networking import NetworkObject, networkManager, NetworkRequestError, \
    fileChunkUpload, MAX_CHUNK_SIZE, FileData
from ...utils import TIME_ZONE
from ...cryptography import getProjectKey, aes


SampleDataType = TypeVar("SampleDataType")


def _relinkSample(samplePath: Path) -> None:
    for datasetPath in folder_manager.datasetsFolder.iterdir():
        linkPath = datasetPath / samplePath.name
        if not linkPath.exists():
            continue

        linkPath.unlink()
        os.link(samplePath, linkPath)


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

        # Decrypt sample
        aes.decryptFile(getProjectKey(self.projectId), self.downloadPath, self.zipPath)

        # Relink sample to all datasets to which it belongs
        _relinkSample(self.zipPath)

    def _download(self, ignoreCache: bool = False) -> None:
        if self.downloadPath.exists() and self.modifiedSinceLastDownload():
            ignoreCache = True

        if ignoreCache and self.downloadPath.exists():
            self.downloadPath.unlink()
            if self.path.exists():
                shutil.rmtree(self.path)

            if self.zipPath.exists() and self.isEncrypted:
                self.zipPath.unlink()

        if not ignoreCache and self.downloadPath.exists():
            return

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

    @override
    def download(self, decrypt: bool = True, ignoreCache: bool = False) -> None:
        """
            Downloads and optionally decrypts sample from Coretex.ai

            Raises
            ------
            NetworkRequestError -> if some kind of error happened during
            the download process
        """

        if decrypt and not self.isEncrypted:
            # Change to false if sample is not encrypted
            decrypt = False

        # Download the sample
        self._download(ignoreCache)

        if decrypt:
            # Decrypt the sample
            self.decrypt(ignoreCache)

        # Update sample download time to now
        os.utime(self.downloadPath, (os.stat(self.downloadPath).st_atime, time.time()))

        # If sample was downloaded succesfully relink it to datasets to which it is linked
        _relinkSample(self.downloadPath)

    @override
    def unzip(self, ignoreCache: bool = False) -> None:
        if not self.downloadPath.exists():
            raise RuntimeError("You must first download the Sample before you can unzip it")

        if not self.zipPath.exists() and self.isEncrypted:
            raise RuntimeError("You must first decrypt the Sample before you can unzip it")

        super().unzip(ignoreCache)

    @override
    def load(self) -> SampleDataType:
        return super().load()  # type: ignore

    @override
    def _updateArchive(self) -> None:
        super()._updateArchive()

        if self.isEncrypted:
            aes.encryptFile(getProjectKey(self.projectId), self.zipPath, self.downloadPath)

    def _overwriteSample(self, samplePath: Path) -> None:
        if not self.isEncrypted:
            raise RuntimeError("Only encrypted samples can be overwriten.")

        with folder_manager.tempFile() as encryptedPath:
            aes.encryptFile(getProjectKey(self.projectId), samplePath, encryptedPath)

            params: Dict[str, Any] = {
                "id": self.id
            }

            files: List[FileData] = []

            # Use chunk upload if file is larger than MAX_CHUNK_SIZE
            # Use normal upload if file is smaller than MAX_CHUNK_SIZE
            size = encryptedPath.stat().st_size

            if size > MAX_CHUNK_SIZE:
                params["file_id"] = fileChunkUpload(encryptedPath)
            else:
                files.append(FileData.createFromPath("file", encryptedPath))

            response = networkManager.formData(f"{self._endpoint()}/upload", params, files, timeout = (5, 300))
            if response.hasFailed():
                raise NetworkRequestError(response, f"Failed to overwrite Sample \"{self.name}\"")
