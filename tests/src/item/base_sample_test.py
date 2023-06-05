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
import os
import shutil

from coretex import Sample


class BaseSampleTest:

    class Base(unittest.TestCase):

        sample: Sample

        def setUp(self) -> None:
            self.sample = self.__class__.sample

        def tearDown(self) -> None:
            if os.path.exists(self.sample.path):
                shutil.rmtree(self.sample.path)

        def test_sampleUnzip(self) -> None:
            if os.path.exists(self.sample.path):
                shutil.rmtree(self.sample.path)

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

        def test_sampleLoad(self) -> None:
            self.assertIsNone(
                self.sample.load(),
                "Base sample load did not return None"
            )
