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

from typing import Optional, Union
from typing_extensions import Self
from pathlib import Path

from ..image_sample import ImageSample


class ComputerVisionSample(ImageSample):

    """
        Represents sample linked to task of type Computer Vision from Coretex.ai
    """

    @classmethod
    def createComputerVisionSample(cls, datasetId: int, imagePath: Union[Path, str]) -> Optional[Self]:
        """
            Creates a new sample from the provided path and adds sample to specified dataset

            Parameters
            ----------
            datasetId : int
                id of dataset to which sample will be added
            imagePath : Union[Path, str]
                path to the sample

            Returns
            -------
            Optional[Self] -> The created sample object or None if creation failed

            Example
            -------
            >>> from coretex import ComputerVisionSample
            \b
            >>> sample = ComputerVisionSample.createComputerVisionSample(1023, "path/to/file.jpeg")
            >>> if sample is None:
                    print("Failed to create computer vision sample")
        """

        return cls.createImageSample(datasetId, imagePath)
