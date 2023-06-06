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

import unittest

from coretex import ComputerVisionSample, ComputerVisionDataset, SpaceTask

from .base_network_sample_test import BaseNetworkSampleTest
from ..base_computer_vision_sample_test import BaseComputerVisionSampleTest
from ...utils import createRemoteEnvironmentFor


class TestImageSample(BaseComputerVisionSampleTest.Base, BaseNetworkSampleTest.Base):

    dataset: ComputerVisionDataset
    sample: ComputerVisionSample

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        space, dataset = createRemoteEnvironmentFor(SpaceTask.computerVision, ComputerVisionDataset)

        cls.space = space
        cls.dataset = dataset
        cls.sample = dataset.samples[0]

    def test_createComputerVisionSample(self) -> None:
        self.sample.unzip()

        sample = ComputerVisionSample.createComputerVisionSample(self.dataset.id, self.sample.imagePath)
        self.assertIsNotNone(sample, "Failed to create computer vision sample")


if __name__ == "__main__":
    unittest.main()
