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

from typing import Union

import unittest
import os
import shutil

from coretex import NetworkSample, LocalSample


class BaseSampleTest:

    class Base(unittest.TestCase):

        sample: Union[NetworkSample, LocalSample]

        def tearDown(self) -> None:
            super().tearDown()

            if os.path.exists(self.sample.path):
                shutil.rmtree(self.sample.path)

            self.assertFalse(os.path.exists(self.sample.path))

        def test_sampleUnzip(self) -> None:
            self.sample.unzip()
            self.assertTrue(
                os.path.exists(self.sample.zipPath),
                "Sample not extracted properly"
            )

            self.sample.unzip(ignoreCache = True)
            self.assertTrue(
                os.path.exists(self.sample.zipPath),
                "Sample not extracted properly"
            )

            self.sample.unzip()
            self.assertTrue(
                os.path.exists(self.sample.zipPath),
                "Sample not extracted properly"
            )
