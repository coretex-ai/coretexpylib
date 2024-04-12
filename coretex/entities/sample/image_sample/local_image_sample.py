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

from typing import Dict, Any
from pathlib import Path

import json

from .image_sample_data import AnnotatedImageSampleData
from .image_format import ImageFormat
from ..local_sample import LocalSample
from ...annotation import CoretexImageAnnotation


class LocalImageSample(LocalSample[AnnotatedImageSampleData]):

    """
        Represents the local Image Sample object\n
        Contains basic properties and functionality for local image Sample classes\n
        The class has several methods that allow users to access and
        manipulate local image data and annotations
    """

    @property
    def imagePath(self) -> Path:
        for format in ImageFormat:
            imagePaths = list(self.path.glob(f"*.{format.extension}"))
            imagePaths = [path for path in imagePaths if not "thumbnail" in str(path)]

            if len(imagePaths) > 0:
                return Path(imagePaths[0])

        raise FileNotFoundError

    @property
    def annotationPath(self) -> Path:
        return self.path / "annotations.json"

    @property
    def metadataPath(self) -> Path:
        return self.path / "metadata.json"

    def load(self) -> AnnotatedImageSampleData:
        """
            Loads image and its annotation if it exists

            Returns
            -------
            AnnotatedImageSampleData -> image data and annotation in Coretex.ai format
        """

        return AnnotatedImageSampleData(self.path)

    def loadMetadata(self) -> Dict[str, Any]:
        """
            Loads sample metadata into a dictionary

            Returns
            -------
            dict[str, Any] -> the metadata as a dict object

            Raises
            ------
            FileNotFoundError -> if metadata file is missing\n
            ValueError -> if json in the metadata file is list
        """

        if not self.metadataPath.exists():
            raise FileNotFoundError(f"Metadata file \"{self.metadataPath}\" not found")

        with self.metadataPath.open("r") as metadataFile:
            metadata = json.load(metadataFile)
            if not isinstance(metadata, dict):
                raise ValueError(f"Metatada for sample \"{self.name}\" is a list. Expected dictionary")

            return metadata

    def saveAnnotation(self, coretexAnnotation: CoretexImageAnnotation) -> bool:
        """
            Updates annotation for the image

            Returns
            -------
            bool -> returns True if successful, False otherwise
        """

        with self.annotationPath.open("w") as file:
            json.dump(coretexAnnotation.encode(), file)

        self._updateArchive()
        return True

    def saveMetadata(self, metadata: Dict[str, Any]) -> None:
        """
            Saves a json object as metadata for the sample

            Parameters
            ----------
            metadata : dict[str, Any]
                Json object containing sample metadata
        """

        with self.metadataPath.open("w") as file:
            json.dump(metadata, file)

        self._updateArchive()
