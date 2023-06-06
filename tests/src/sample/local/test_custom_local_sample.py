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

from coretex import LocalCustomSample, LocalCustomDataset, SpaceTask

from ..base_sample_test import BaseSampleTest
from ...utils import createLocalEnvironmentFor


class TestCustomLocalSample(BaseSampleTest.Base):

    sample: LocalCustomSample

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        dataset = createLocalEnvironmentFor(SpaceTask.other, LocalCustomDataset)
        cls.sample = dataset.samples[0]


if __name__ == "__main__":
    unittest.main()
