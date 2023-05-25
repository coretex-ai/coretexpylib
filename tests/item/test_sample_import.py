#     Copyright (C) 2023  BioMech LLC

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

import unittest
import time

from coretex import ImageSegmentationSample, ComputerVisionSample, ImageSegmentationDataset, ComputerVisionDataset, CustomDataset, CustomSample

from config import OTHER_SPACE_ID, IMAGE_SEGMENTATION_SPACE_ID, COMPUTER_VISION_SPACE_ID
from base_network_test import BaseNetworkTest


class TestNetworkSample(BaseNetworkTest.Base):  # type: ignore

    def test_createCustomSample(self) -> None:
        dataset = CustomDataset.createDataset(f"PythonUnitTest {time.time()}", OTHER_SPACE_ID)
        self.assertIsNotNone(dataset, "Failed to create dataset")

        sample = CustomSample.createCustomSample(f"PythonUnitTest {time.time()}", dataset.id, "./tests/resources/local_sample.zip")
        self.assertIsNotNone(sample, "Failed to create image segmentation sample")

        result = dataset.delete()
        self.assertTrue(result, "Failed to delete dataset")

    def test_createImageSegmentationSample(self) -> None:
        dataset = ImageSegmentationDataset.createDataset(f"PythonUnitTest {time.time()}", IMAGE_SEGMENTATION_SPACE_ID)
        self.assertIsNotNone(dataset, "Failed to create dataset")

        sample = ImageSegmentationSample.createImageSegmentationSample(dataset.id, "./tests/resources/image.jpeg")
        self.assertIsNotNone(sample, "Failed to create image segmentation sample")

        result = dataset.delete()
        self.assertTrue(result, "Failed to delete dataset")

    def test_createComputerVisionSample(self) -> None:
        dataset = ComputerVisionDataset.createDataset(f"PythonUnitTest {time.time()}", COMPUTER_VISION_SPACE_ID)
        self.assertIsNotNone(dataset, "Failed to create dataset")

        sample = ComputerVisionSample.createComputerVisionSample(dataset.id, "./tests/resources/image.jpeg")
        self.assertIsNotNone(sample, "Failed to create image segmentation sample")

        result = dataset.delete()
        self.assertTrue(result, "Failed to delete dataset")


if __name__ == "__main__":
    unittest.main()
