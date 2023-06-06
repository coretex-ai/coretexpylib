# #     Copyright (C) 2023  Coretex LLC

# #     This file is part of Coretex.ai

# #     This program is free software: you can redistribute it and/or modify
# #     it under the terms of the GNU Affero General Public License as
# #     published by the Free Software Foundation, either version 3 of the
# #     License, or (at your option) any later version.

# #     This program is distributed in the hope that it will be useful,
# #     but WITHOUT ANY WARRANTY; without even the implied warranty of
# #     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# #     GNU Affero General Public License for more details.

# #     You should have received a copy of the GNU Affero General Public License
# #     along with this program.  If not, see <https://www.gnu.org/licenses/>.

# from typing import Optional

# import unittest

# from coretex import ImageSample, ImageDataset

# from .base_network_dataset_test import BaseNetworkDatasetTest
# from .test_image_dataset_local import TestImageDatasetLocal


# class TestImageDataset(TestImageDatasetLocal, BaseNetworkDatasetTest.Base):

#     dataset: ImageDataset  # type: ignore

#     def setUp(self) -> None:
#         super().setUp()

#         dataset: Optional[ImageDataset[ImageSample]] = ImageDataset.fetchById(2421)
#         if dataset is None:
#             raise ValueError

#         self.dataset = dataset
#         self.sampleType = ImageSample

#     def test_saveClasses(self) -> None:
#         super().test_saveClasses()

#         fetchedDataset: Optional[ImageDataset[ImageSample]] = ImageDataset.fetchById(self.dataset.id)
#         self.assertIsNotNone(fetchedDataset)

#         # here only for mypy
#         if fetchedDataset is None:
#             raise ValueError

#         self.compareClasses(fetchedDataset.classes, self.dataset.classes)


# if __name__ == "__main__":
#     unittest.main()
