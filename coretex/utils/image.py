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


def resizeWithPadding(
    image: np.ndarray,
    newShape: Tuple[int, int]
) -> Tuple[np.ndarray, Tuple[int, int]]:

    originalShape = (image.shape[1], image.shape[0])
    ratio = max(newShape) / max(originalShape)
    newSize = tuple([int(x * ratio) for x in originalShape])
    resizedImage = Image.fromarray(image).resize(newSize)

    deltaW = newShape[0] - newSize[0]
    deltaH = newShape[1] - newSize[1]

    top = deltaH // 2
    left = deltaW // 2

    paddedImage = Image.new(resizedImage.mode, (newShape[1], newShape[0]), 0)
    paddedImage.paste(resizedImage, (left, top))

    return np.array(paddedImage), (top, left)
