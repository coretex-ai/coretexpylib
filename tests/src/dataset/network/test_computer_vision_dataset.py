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

# import unittest

# from coretex import ComputerVisionDataset, ComputerVisionSample, ProjectType

# from .base_network_dataset_test import BaseNetworkDatasetTest
# from ..base_computer_vision_dataset_test import BaseComputerVisionDatasetTest
# from ...utils import createRemoteEnvironmentFor


# class TestComputerVisionDataset(BaseComputerVisionDatasetTest.Base[ComputerVisionDataset], BaseNetworkDatasetTest.Base[ComputerVisionDataset]):

#     @classmethod
#     def setUpClass(cls) -> None:
#         super().setUpClass()

#         project, dataset = createRemoteEnvironmentFor(ProjectType.computerVision, ComputerVisionDataset)

#         cls.project = project
#         cls.dataset = dataset
#         cls.sampleType = ComputerVisionSample

#     def test_saveClasses(self) -> None:
#         super().test_saveClasses()

#         fetchedDataset = ComputerVisionDataset.fetchById(self.dataset.id)
#         self.compareClasses(fetchedDataset.classes, self.dataset.classes)


# if __name__ == "__main__":
#     unittest.main()
