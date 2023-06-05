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
from ..space import SpaceTask
from ...codable import KeyDescriptor
from ...networking import NetworkObject, networkManager, FileData
from ...folder_management import FolderManager
from ...utils import guessMimeType


SampleDataType = TypeVar("SampleDataType")


class NetworkSample(Generic[SampleDataType], Sample[SampleDataType], NetworkObject):

    """
        Represents a base class for all Sample classes which are
        comunicating with Coretex.ai
    """

    isLocked: bool
    spaceTask: SpaceTask

    @property
    def path(self) -> str:
        """
            Returns
            -------
            str -> path for network sample
        """

        return os.path.join(FolderManager.instance().samplesFolder, str(self.id))

    @property
    def zipPath(self) -> str:
        """
            Returns
            -------
            str -> zip path for network sample
        """

        return f"{self.path}.zip"

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["spaceTask"] = KeyDescriptor("project_task", SpaceTask)

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

        if os.path.exists(self.zipPath) and not ignoreCache:
            return True

        response = networkManager.genericDownload(
            endpoint = f"{self.__class__._endpoint()}/export?id={self.id}",
            destination = self.zipPath
        )

        return not response.hasFailed()

    def load(self) -> SampleDataType:
        return super().load()  # type: ignore
