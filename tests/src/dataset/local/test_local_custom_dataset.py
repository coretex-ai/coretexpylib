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

from typing import Generator
from pathlib import Path

import unittest

from coretex import LocalCustomSample, LocalCustomDataset, ProjectType

from ..base_dataset_test import BaseDatasetTest
from ...utils import createLocalEnvironmentFor


class TestLocalCustomDataset(BaseDatasetTest.Base[LocalCustomDataset]):

    def setUp(self) -> None:
        super().setUp()

        self.dataset = createLocalEnvironmentFor(ProjectType.other, LocalCustomDataset)
        self.sampleType = LocalCustomSample

    def test_loadDefault(self) -> None:
        datasetPath = Path("./tests/resources/other_dataset")
        dataset = LocalCustomDataset.default(datasetPath)

        self.assertEqual(dataset.count, 2)

    def test_loadCustom(self) -> None:
        def generator(path: Path) -> Generator[LocalCustomSample, None, None]:
            for samplePath in path.glob("*.zip"):
                yield LocalCustomSample(samplePath)

        datasetPath = Path("./tests/resources/other_dataset")
        dataset = LocalCustomDataset.custom(datasetPath, generator(datasetPath))

        self.assertEqual(dataset.count, 2)


if __name__ == "__main__":
    unittest.main()
