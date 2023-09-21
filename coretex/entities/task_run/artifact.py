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

from typing import Optional, Dict, List, Union
from typing_extensions import Self
from enum import IntEnum
from pathlib import Path

from ... import folder_manager
from ...codable import Codable, KeyDescriptor
from ...networking import networkManager, RequestType, FileData
from ...utils import guessMimeType


class ArtifactType(IntEnum):

    """
        Available types of Artifacts on Coretex
    """

    directory = 1
    file      = 2


class Artifact(Codable):

    """
        Artifact class represents a single result of a run\n
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
        taskRunId : int
            id of run
    """

    artifactType: ArtifactType
    remoteFilePath: str
    size: Optional[int]
    mimeType: str
    timestamp: int
    taskRunId: int

    @property
    def localFilePath(self) -> Path:
        """
            Represents the local path of the Artifact

            Returns
            -------
            Path -> local path to Artifact
        """

        return folder_manager.getArtifactsFolder(self.taskRunId) / self.remoteFilePath

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
        descriptors["taskRunId"] = KeyDescriptor(isEncodable = False)

        return descriptors

    @classmethod
    def create(
        cls,
        taskRunId: int,
        localFilePath: Union[Path, str],
        remoteFilePath: str,
        mimeType: Optional[str] = None
    ) -> Optional[Self]:

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
            "model_queue_id": taskRunId,
            "path": remoteFilePath
        }

        response = networkManager.genericUpload("artifact/upload-file", files, parameters)
        if response.hasFailed():
            return None

        artifact = cls.decode(response.json)
        artifact.taskRunId = taskRunId

        return artifact

    def download(self) -> bool:
        """
            Downloads Artifact from Coretex.ai

            Returns
            -------
            bool -> False if response has failed, True otherwise
        """

        return not networkManager.genericDownload(
            f"artifact/download-file?path={self.remoteFilePath}&model_queue_id={self.taskRunId}",
            str(self.localFilePath)
        ).hasFailed()

    @classmethod
    def fetchAll(cls, taskRunId: int, path: Optional[str] = None, recursive: bool = False) -> List[Self]:
        """
            Fetch all Artifacts from Coretex.ai for the specified run

            Parameters
            ----------
            taskRunId : int
                id of run
            path : Optional[str]
                local path where u want to store fetched Artifacts
            recursive : bool
                True if you want list to be sorted recursively, False otherwise
        """

        queryParameters = [
            f"model_queue_id={taskRunId}"
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

        artifacts = [cls.decode(element) for element in response.json]

        for artifact in artifacts:
            artifact.taskRunId = taskRunId

            if recursive and artifact.isDirectory:
                artifacts.extend(
                    cls.fetchAll(taskRunId, artifact.remoteFilePath)
                )

        return artifacts
