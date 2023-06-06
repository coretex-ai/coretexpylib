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

from typing import Type, Generic, TypeVar

import unittest

from coretex import Dataset, Sample

from ..utils import generateUniqueName


DatasetType = TypeVar("DatasetType", bound = "Dataset")


class BaseDatasetTest:

    class Base(unittest.TestCase, Generic[DatasetType]):

        dataset: DatasetType
        sampleType: Type[Sample]

        @classmethod
        def setUpClass(cls) -> None:
            super().setUpClass()

        def test_sampleType(self) -> None:
            for sample in self.dataset.samples:
                self.assertIsInstance(sample, self.sampleType)

        def test_count(self) -> None:
            self.assertEqual(self.dataset.count, len(self.dataset.samples))

        def test_rename(self) -> None:
            newName = generateUniqueName()
            self.dataset.rename(newName)

            self.assertEqual(self.dataset.name, newName)
