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

# from typing import TypeVar, Generic

# import os
# import shutil

# from coretex import NetworkDataset, Space

# from ..base_dataset_test import BaseDatasetTest
# from ...base_network_test import BaseNetworkTest


# DatasetType = TypeVar("DatasetType", bound = NetworkDataset)


# class BaseNetworkDatasetTest:

#     class Base(BaseDatasetTest.Base[DatasetType], BaseNetworkTest.Base, Generic[DatasetType]):

#         space: Space

#         @classmethod
#         def tearDownClass(cls) -> None:
#             super().tearDownClass()

#             for sample in cls.dataset.samples:
#                 if os.path.exists(sample.path):
#                     shutil.rmtree(sample.path)

#                 if os.path.exists(sample.zipPath):
#                     os.unlink(sample.zipPath)

#             if os.path.exists(cls.dataset.path):
#                 shutil.rmtree(cls.dataset.path)

#             # TODO: Enable this once delete is working on backend
#             # if not cls.space.delete():
#             #     raise RuntimeError(">> [Coretex] Failed to delete space")

#         def test_networkDatasetDownload(self) -> None:
#             def verify() -> None:
#                 self.assertTrue(
#                     os.path.exists(self.dataset.path),
#                     "Dataset not downloaded"
#                 )

#                 for sample in self.dataset.samples:
#                     self.assertTrue(
#                         os.path.exists(sample.zipPath),
#                         f"Sample {sample.id} not downloaded"
#                     )

#             self.dataset.download()
#             verify()

#             self.dataset.download(ignoreCache = True)
#             verify()

#             self.dataset.download()
#             verify()
