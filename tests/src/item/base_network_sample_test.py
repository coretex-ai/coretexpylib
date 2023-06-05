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

import os

from coretex import NetworkSample

from .base_sample_test import BaseSampleTest
from ..base_network_test import BaseNetworkTest


class BaseNetworkSampleTest:

    class Base(BaseSampleTest.Base, BaseNetworkTest.Base):

        sample: NetworkSample

        def test_sampleUnzip(self) -> None:
            self.sample.download(ignoreCache = True)

            super().test_sampleUnzip()

        def test_networkSampleDownload(self) -> None:
            if os.path.exists(self.sample.zipPath):
                os.unlink(self.sample.zipPath)

            self.sample.download()
            self.assertTrue(
                os.path.exists(self.sample.zipPath),
                "Sample not downloaded"
            )

            self.sample.download(ignoreCache = True)
            self.assertTrue(
                os.path.exists(self.sample.zipPath),
                "Sample not downloaded"
            )

            self.sample.download()
            self.assertTrue(
                os.path.exists(self.sample.zipPath),
                "ItSampleem not downloaded"
            )
