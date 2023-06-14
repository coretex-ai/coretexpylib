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

# import os

# from coretex import Space, NetworkSample, NetworkDataset

# from ..base_sample_test import BaseSampleTest
# from ...base_network_test import BaseNetworkTest


# class BaseNetworkSampleTest:

#     class Base(BaseSampleTest.Base, BaseNetworkTest.Base):

#         space: Space
#         dataset: NetworkDataset
#         sample: NetworkSample

#         @classmethod
#         def tearDownClass(cls) -> None:
#             super().tearDownClass()

#             # TODO: Enable this once delete is working on backend
#             # if not cls.space.delete():
#             #     raise RuntimeError(">> [Coretex] Failed to delete space")

#         def setUp(self) -> None:
#             super().setUp()

#             result = self.sample.download(ignoreCache = True)
#             self.assertIsNotNone(result, "Failed to download sample")

#         def tearDown(self) -> None:
#             super().tearDown()

#             if os.path.exists(self.sample.zipPath):
#                 os.unlink(self.sample.zipPath)

#             self.assertFalse(os.path.exists(self.sample.zipPath), "Failed to cleanup sample")

#         def test_networkSampleDownload(self) -> None:
#             self.assertTrue(
#                 self.sample.download(),
#                 "Failed to download sample"
#             )

#             self.assertTrue(
#                 os.path.exists(self.sample.zipPath),
#                 "Sample not properly downloaded"
#             )

#             self.assertTrue(
#                 self.sample.download(ignoreCache = True),
#                 "Failed to download sample"
#             )

#             self.assertTrue(
#                 os.path.exists(self.sample.zipPath),
#                 "Sample not properly downloaded"
#             )

#             self.assertTrue(
#                 self.sample.download(),
#                 "Failed to download sample"
#             )

#             self.assertTrue(
#                 os.path.exists(self.sample.zipPath),
#                 "Sample not properly downloaded"
#             )
