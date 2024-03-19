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

from typing import Tuple

from PIL import Image

import numpy as np


def resizeWithPadding(image: np.ndarray, width: int, height: int) -> Tuple[np.ndarray, int, int]:
    """
        Resizes the image while maintaining original aspect ratio,
        and filling the remaining space with symmetrical padding so
        that the original image is in the center

        Parameters
        ----------
        image : np.ndarray
            Input image as an array
        width : int
            Width of the output image
        height : int
            Height of the output image

        Returns
        -------
        Tuple[np.ndarray, int, int] -> Output image as numpy array,
        number of pixels of padding from top/bottom and number of pixels
        of padding from left/right
    """

    originalWidth = image.shape[1]
    originalHeight = image.shape[0]

    ratio = max(width, height) / max(originalWidth, originalHeight)

    newWidth = int(originalWidth * ratio)
    newHeight = int(originalHeight * ratio)

    resizedImage = Image.fromarray(image).resize((newWidth, newHeight))

    deltaW = width - newWidth
    deltaH = height - newHeight

    top = deltaH // 2
    left = deltaW // 2

    paddedImage = Image.new(resizedImage.mode, (width, height), 0)
    paddedImage.paste(resizedImage, (left, top))

    return np.array(paddedImage), top, left


def cropToWidth(image: np.ndarray) -> np.ndarray:
    """
        Crops the image to width while maintaining the center

        Parameters
        ----------
        image : np.ndarray
            Input image as an array

        Returns
        -------
        np.ndarray -> Output image that has been croped vertically
        to width
    """

    height, width = image.shape[:2]
    if height > width:
        startY = (height - width) // 2
        endY = startY + width
        image = image[startY:endY, 0:width]

    return image
