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

from typing import Any, Dict

from .image_sample_data import AnnotatedImageSampleData
from .local_image_sample import LocalImageSample
from ..network_sample import NetworkSample
from ...annotation import CoretexImageAnnotation
from ....networking import networkManager, NetworkRequestError


class ImageSample(NetworkSample[AnnotatedImageSampleData], LocalImageSample):

    """
        Represents the generic image sample\n
        Contains basic properties and functionality for all image sample classes\n
        The class has several methods that allow users to access and
        manipulate image data and annotations, as well as to create new image samples
    """

    def __init__(self) -> None:
        NetworkSample.__init__(self)

    def saveAnnotation(self, coretexAnnotation: CoretexImageAnnotation) -> bool:
        # Encrypted sample must be downloaded for annotation to be updated
        if self.isEncrypted:
            self.download(decrypt = True)

        # Only save annotation locally if it is downloaded
        if self.zipPath.exists():
            self.unzip()

            super().saveAnnotation(coretexAnnotation)

        if self.isEncrypted:
            try:
                self._overwriteSample(self.zipPath)
                return True
            except NetworkRequestError:
                return False
        else:
            parameters = {
                "id": self.id,
                "data": coretexAnnotation.encode()
            }

            response = networkManager.post("session/save-annotations", parameters)
            return not response.hasFailed()

    def saveMetadata(self, metadata: Dict[str, Any]) -> None:
        # Encrypted sample must be downloaded for metadata to be updated
        if self.isEncrypted:
            self.download(decrypt = True)

        # Only save metadata locally if it is downloaded
        if self.zipPath.exists():
            self.unzip()

            super().saveMetadata(metadata)

        if self.isEncrypted:
            self._overwriteSample(self.zipPath)
        else:
            parameters = {
                "id": self.id,
                "data": metadata
            }

            response = networkManager.post("session/save-metadata", parameters)
            if response.hasFailed():
                raise NetworkRequestError(response, f"Failed to upload metadata for sample \"{self.name}\"")
