from typing import Final, Any, Optional
from pathlib import Path

import json

from PIL import Image

import numpy as np

from .image_format import ImageFormat
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

from ...annotation import CoretexImageAnnotation, ImageDatasetClasses


def _findImage(path: Path) -> Path:
    for format in ImageFormat:
        imagePaths = list(path.glob(f"*.{format.extension}"))
        imagePaths = [path for path in imagePaths if not "thumb" in str(path)]

        if len(imagePaths) > 0:
            return Path(imagePaths[0])

    raise RuntimeError


def _readImageData(path: Path) -> np.ndarray:
    image = Image.open(path)
    if image.mode != "RGB":
        image = image.convert("RGB")

    imageData = np.frombuffer(image.tobytes(), dtype = np.uint8)
    imageData = imageData.reshape((image.size[1], image.size[0], 3))

    return imageData


def _readAnnotationData(path: Path) -> CoretexImageAnnotation:
    with open(path, "r") as annotationsFile:
        return CoretexImageAnnotation.decode(
            json.load(annotationsFile)
        )


class AnnotatedImageSampleData:

    """
        Contains image data as well as its annotation\n
        Annotation is expected to be in Coretex.ai format
    """

    def __init__(self, path: Path) -> None:
        self.image: Final = _readImageData(_findImage(path))
        self.annotation: Optional[CoretexImageAnnotation] = None

        annotationPath = path / "annotations.json"
        if annotationPath.exists():
            self.annotation = _readAnnotationData(annotationPath)

    def extractSegmentationMask(self, classes: ImageDatasetClasses) -> np.ndarray:
        """
            Generates segmentation mask for the provided classes

            Parameters
            ----------
            classes : ImageDatasetClasses
                list of dataset classes

            Returns
            -------
            np.ndarray -> segmentation mask represented as np.ndarray
        """

        if self.annotation is None:
            raise ValueError

        return self.annotation.extractSegmentationMask(classes)
