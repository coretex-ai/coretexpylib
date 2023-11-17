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

from typing import List, Tuple
from typing_extensions import Self
from pathlib import Path
from zipfile import ZipFile

import copy
import json

from PIL import Image
from PIL.Image import Image as PILImage
from numpy import ndarray

import numpy as np

from .base import BaseImageDataset
from ...sample import ImageSample, AnnotatedImageSampleData
from ...annotation import CoretexSegmentationInstance, CoretexImageAnnotation, BBox
from .... import folder_manager


ANNOTATION_NAME = "annotations.json"


class AugmentedImageSample(ImageSample):

    @property
    def path(self) -> Path:
        """
            Returns
            -------
            Path -> path to new augmented samples directory
        """

        return folder_manager.temp / "temp-augmented-ds" / str(self.id)

    @classmethod
    def createFromSample(cls, sample: ImageSample) -> Self:
        """
            Creates exact copy of sample from provided sample

            Parameters
            ----------
            sample : ImageSample
                sample object

            Returns
            -------
            Self -> sample object
        """

        obj = cls()

        for key, value in sample.__dict__.items():
            obj.__dict__[key] = copy.deepcopy(value)

        return obj


def isOverlapping(
    x: int,
    y: int,
    image: PILImage,
    locations: List[Tuple[int, int, int, int]]
) -> bool:

    for loc in locations:
        if (x < loc[0] + loc[2] and x + image.width > loc[0] and
            y < loc[1] + loc[3] and y + image.height > loc[1]):

            return True

    return False


def generateSegmentedImage(image: np.ndarray, segmentationMask: np.ndarray) -> Image:
    rgbaImage = Image.fromarray(image).convert("RGBA")

    segmentedImage = np.asarray(rgbaImage) * segmentationMask
    segmentedImage = Image.fromarray(segmentedImage)

    alpha = segmentedImage.getchannel("A")
    bbox = alpha.getbbox()
    croppedImage = segmentedImage.crop(bbox)

    return croppedImage


def composeImage(
    segmentedImages: List[PILImage],
    backgroundImage: np.ndarray,
    angle: int,
    scale: float
) -> Tuple[PILImage, List[Tuple[int, int]]]:

    centroids: List[Tuple[int, int]] = []
    locations: List[Tuple[int, int, int, int]] = []

    background = Image.fromarray(backgroundImage)

    for segmentedImage in segmentedImages:
        image = segmentedImage

        rotatedImage = image.rotate(angle, expand = True)
        resizedImage = rotatedImage.resize((int(rotatedImage.width * scale), int(rotatedImage.height * scale)))

        # Calculate the maximum x and y coordinates for the top left corner of the image
        maxX = background.width - resizedImage.width
        maxY = background.height - resizedImage.height

        while True:
            # Generate a random location within the bounds of the background image
            x = np.random.randint(0, maxX)
            y = np.random.randint(0, maxY)

            # Check if the image overlaps with any previously pasted images
            if not isOverlapping(x, y, resizedImage, locations):
                break

        background.paste(resizedImage, (x, y), resizedImage)

        centerX = x + resizedImage.width // 2
        centerY = y + resizedImage.height // 2

        centroids.append((centerX, centerY))

        # Add the location to the list
        locations.append((x, y, resizedImage.width, resizedImage.height))

    return background, centroids


def processInstance(
    sample: ImageSample,
    backgroundSampleData: AnnotatedImageSampleData,
    angle: int,
    scale: float
) -> Tuple[PILImage, List[CoretexSegmentationInstance]]:

    segmentedImages: List[PILImage] = []
    augmentedInstances: List[CoretexSegmentationInstance]= []

    sampleData = sample.load()
    if sampleData.annotation is None:
        raise RuntimeError(f"CTX sample dataset sample id: {sample.id} image doesn't exist!")

    for instance in sampleData.annotation.instances:
        foregroundMask = instance.extractBinaryMask(sampleData.image.shape[1], sampleData.image.shape[0])
        segmentedImage = generateSegmentedImage(sampleData.image, foregroundMask)

        segmentedImages.append(segmentedImage)

    composedImage, centroids = composeImage(segmentedImages, backgroundSampleData.image, angle, scale)

    for i, instance in enumerate(sampleData.annotation.instances):
        segmentationsFlatten = [sample for sublist in instance.segmentations for sample in sublist]
        augmentedInstance = CoretexSegmentationInstance.create(instance.classId, BBox.fromPoly(segmentationsFlatten), instance.segmentations)

        augmentedInstance.rotateSegmentations(angle)
        augmentedInstance.centerSegmentations(centroids[i])

        augmentedInstances.append(augmentedInstance)

    return composedImage, augmentedInstances


def processSample(
    sample: ImageSample,
    backgroundSample: ImageSample,
    angle: int,
    scale: float
) -> Tuple[ndarray, CoretexImageAnnotation]:

    backgroundSampleData = backgroundSample.load()

    composedImage, augmentedInstances = processInstance(sample, backgroundSampleData, angle, scale)
    annotation = CoretexImageAnnotation.create(sample.name, composedImage.width, composedImage.height, augmentedInstances)

    return composedImage, annotation


def storeFiles(
    tempPath: Path,
    augmentedSample: ImageSample,
    augmentedImage: PILImage,
    annotation: CoretexImageAnnotation
) -> None:

    imagePath = tempPath / f"{augmentedSample.name}.jpeg"
    annotationPath = tempPath / ANNOTATION_NAME
    zipPath = tempPath / f"{augmentedSample.id}"

    augmentedImage.save(imagePath)

    with open(annotationPath, 'w') as annotationfile:
        jsonObject = json.dumps(annotation.encode())
        annotationfile.write(jsonObject)

    with ZipFile(zipPath.with_suffix(".zip"), mode = "w") as archive:
        archive.write(imagePath, f"{augmentedSample.name}.jpeg")
        archive.write(annotationPath, ANNOTATION_NAME)

    imagePath.unlink(missing_ok = True)
    annotationPath.unlink(missing_ok = True)


def augmentDataset(
    normalDataset: BaseImageDataset,
    backgroundDataset: BaseImageDataset,
    angle: int = 0,
    scale: float = 1.0
) -> None:
    """
        Modifies normalDataset by adding new augmented samples to it

        Parameters
        ----------
        normalDataset : BaseImageDataset
            BaseImageDataset object
        backgroundDataset : BaseImageDataset
            BaseImageDataset object
        angle : int
            angle of rotation in degrees
        scale : float
            scaling factor
    """

    tempPath = folder_manager.createTempFolder("temp-augmented-ds")
    augmentedSamples: List[AugmentedImageSample] = []

    for i, background in enumerate(backgroundDataset.samples):
        background.unzip()

        for j, sample in enumerate(normalDataset.samples):
            sample.unzip()
            augmentedImage, annotations = processSample(sample, background, angle, scale)

            augmentedSample = AugmentedImageSample.createFromSample(sample)
            augmentedSample.id = int(f"{i}{j}{augmentedSample.id}")

            storeFiles(tempPath, augmentedSample, augmentedImage, annotations)

            augmentedSamples.append(augmentedSample)

    for sample in augmentedSamples:
        normalDataset.samples.append(sample)
