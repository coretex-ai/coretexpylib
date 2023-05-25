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

from pathlib import Path

import unittest
import json

from coretex import LocalImageSample, LocalImageDataset, ImageDatasetClasses, ImageDatasetClass

from .base_dataset_test import BaseDatasetTest


class TestImageDatasetLocal(BaseDatasetTest.Base):

    dataset: LocalImageDataset

    def setUp(self) -> None:
        super().setUp()

        self.dataset = LocalImageDataset(Path("./tests/resources/local_dataset"), LocalImageSample)
        self.sampleType = LocalImageSample

    def compareClasses(self, first: ImageDatasetClasses, second: ImageDatasetClasses) -> None:
        for firstClass in first:
            secondClass = second.classById(firstClass.classIds[0])
            self.assertIsNotNone(secondClass)

            # here only for mypy
            if secondClass is None:
                raise ValueError

            self.assertEqual(firstClass.label, secondClass.label)
            self.assertEqual(firstClass.color, secondClass.color)
            self.assertEqual(firstClass.classIds, secondClass.classIds)

    def test_saveClasses(self) -> None:
        classes = ImageDatasetClass.generate({"test_class_1", "test_class_2"})
        self.dataset.saveClasses(classes)

        self.assertTrue(self.dataset.classesPath.exists())

        with open(self.dataset.classesPath, "r") as classesFile:
            loadedClasses = ImageDatasetClasses([ImageDatasetClass.decode(element) for element in json.load(classesFile)])

        self.assertEqual(len(classes), len(loadedClasses))
        self.compareClasses(classes, loadedClasses)


if __name__ == "__main__":
    unittest.main()
