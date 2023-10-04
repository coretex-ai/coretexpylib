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
from pathlib import Path

import os

from .sample import Sample
from ..project import ProjectType
from ... import folder_manager
from ...codable import KeyDescriptor
from ...networking import NetworkObject, networkManager, FileData


SampleDataType = TypeVar("SampleDataType")


class NetworkSample(Generic[SampleDataType], Sample[SampleDataType], NetworkObject):

    """
        Represents a base class for all Sample classes which are
        comunicating with Coretex.ai
    """

    isLocked: bool
    projectType: ProjectType

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

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["projectType"] = KeyDescriptor("project_task", ProjectType)

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

        response = networkManager.genericUpload("session/import", files, parameters)
        if response.hasFailed():
            return None

        return cls.decode(response.json)

    def download(self, ignoreCache: bool = False) -> bool:
        """
            Downloads sample from Coretex.ai

            Returns
            -------
            bool -> False if response is failed, True otherwise
        """

        response = networkManager.sampleDownload(
            endpoint = f"{self.__class__._endpoint()}/export?id={self.id}",
            destination = self.zipPath,
            ignoreCache = ignoreCache
        )

        # If sample was downloaded succesfully relink it to datasets to which it is linked
        if not response.hasFailed():
            for datasetPath in folder_manager.datasetsFolder.iterdir():
                sampleHardLinkPath = datasetPath / self.zipPath.name
                if not sampleHardLinkPath.exists():
                    continue

                sampleHardLinkPath.unlink()
                os.link(self.zipPath, sampleHardLinkPath)

        return not response.hasFailed()

    def load(self) -> SampleDataType:
        return super().load()  # type: ignore
