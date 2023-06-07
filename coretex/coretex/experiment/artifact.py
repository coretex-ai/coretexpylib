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

from __future__ import annotations

from enum import IntEnum
from typing import Optional, Dict, List
from pathlib import Path

import os

from ...codable import Codable, KeyDescriptor
from ...networking import networkManager, RequestType, FileData
from ...folder_management import FolderManager
from ...utils import guessMimeType


class ArtifactType(IntEnum):

    """
        Available types of Artifacts on Coretex
    """

    directory = 1
    file      = 2

    @staticmethod
    def typeForPath(path: str) -> ArtifactType:
        """
            Retrieve ArtifactType based on provided path

            Parameters
            ----------
            path : str
                path to Artifact
        """

        if os.path.isdir(path):
            return ArtifactType.directory

        if os.path.isfile(path):
            return ArtifactType.file

        raise RuntimeError(">> [Coretex] Unreachable")


class Artifact(Codable):

    """
        Artifact class represents a single result of an experiment\n
        Result can be file of any kind

        Properties
        ----------
        artifactType : ArtifactType
            type of Artifact
        remoteFilePath : str
            path of Artifact on Coretex
        size : Optional[int]
            size of Artifact in bytes (not required)
        mimeType : str
            mimeType of Artifact
        timestamp : int
            current timestamp
        experimentId : int
            id of experiment
    """

    artifactType: ArtifactType
    remoteFilePath: str
    size: Optional[int]
    mimeType: str
    timestamp: int
    experimentId: int

    @property
    def localFilePath(self) -> Path:
        """
            Represents the local path of the Artifact

            Returns
            -------
            Path -> local path to Artifact
        """

        return FolderManager.instance().getArtifactsFolder(self.experimentId) / self.remoteFilePath

    @property
    def isDirectory(self) -> bool:
        """
            Returns
            -------
            bool -> True if Artifact type is directory
        """

        return self.artifactType == ArtifactType.directory

    @property
    def isFile(self) -> bool:
        """
            Returns
            -------
            bool -> True if Artifact type is file
        """

        return self.artifactType == ArtifactType.file

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["artifactType"] = KeyDescriptor("type", ArtifactType)
        descriptors["remoteFilePath"] = KeyDescriptor("path")
        descriptors["timestamp"] = KeyDescriptor("ts")
        descriptors["experimentId"] = KeyDescriptor(isEncodable = False)

        return descriptors

    @classmethod
    def create(cls, experimentId: int, localFilePath: str, remoteFilePath: str, mimeType: Optional[str] = None) -> Optional[Artifact]:
        if mimeType is None:
            # If guessing fails, fallback to binary type
            try:
                mimeType = guessMimeType(localFilePath)
            except:
                mimeType = "application/octet-stream"

        files = [
            FileData.createFromPath("file", localFilePath, mimeType = mimeType)
        ]

        parameters = {
            "model_queue_id": experimentId,
            "path": remoteFilePath
        }

        response = networkManager.genericUpload("artifact/upload-file", files, parameters)
        if response.hasFailed():
            return None

        artifact = Artifact.decode(response.json)
        artifact.experimentId = experimentId

        return artifact

    def download(self) -> bool:
        """
            Downloads Artifact from Coretex.ai

            Returns
            -------
            bool -> False if response has failed, True otherwise
        """

        artifactsFolder = FolderManager.instance().getArtifactsFolder(self.experimentId)
        if not artifactsFolder.exists():
            artifactsFolder.mkdir(parents = True, exist_ok = True)

        return not networkManager.genericDownload(
            f"artifact/download-file?path={self.remoteFilePath}&model_queue_id={self.experimentId}",
            str(self.localFilePath)
        ).hasFailed()

    @classmethod
    def fetchAll(cls, experimentId: int, path: Optional[str] = None, recursive: bool = False) -> List[Artifact]:
        """
            Fetch all Artifacts from Coretex.ai for the specified experiment

            Parameters
            ----------
            experimentId : int
                id of experiment
            path : Optional[str]
                local path where u want to store fetched Artifacts
            recursive : bool
                True if you want list to be sorted recursively, False otherwise
        """

        queryParameters = [
            f"model_queue_id={experimentId}"
        ]

        if path is not None:
            queryParameters.append(f"path={path}")

        parameters = "&".join(queryParameters)
        response = networkManager.genericJSONRequest(
            f"artifact/list-contents?{parameters}",
            RequestType.get
        )

        if response.hasFailed():
            return []

        artifacts = [Artifact.decode(element) for element in response.json]

        for artifact in artifacts:
            artifact.experimentId = experimentId

            if recursive and artifact.isDirectory:
                artifacts.extend(
                    cls.fetchAll(experimentId, artifact.remoteFilePath)
                )

        return artifacts
