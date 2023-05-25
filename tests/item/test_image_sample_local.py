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

from coretex import LocalImageSample, AnnotatedImageSampleData, CoretexImageAnnotation, CoretexSegmentationInstance

from .base_sample_test import BaseSampleTest


class TestImageSampleLocal(BaseSampleTest.Base):

    sample: LocalImageSample

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.sample = LocalImageSample(Path("./tests/resources/local_sample.zip"))

    def test_sampleLoad(self) -> None:
        self.sample.unzip(ignoreCache = True)

        data = self.sample.load()
        self.assertTrue(
            isinstance(data, AnnotatedImageSampleData),
            "Loaded data object is not of type AnnotatedImageSampleData"
        )

        # here only for mypy
        if data.annotation is None:
            raise ValueError

        self.assertEqual(len(data.image.shape), 3, "Loaded image data does not have expected shape")

        height, width, channels = data.image.shape

        self.assertEqual(width, data.annotation.width, "Image width and annotation width do not match")
        self.assertEqual(height, data.annotation.height, "Image height and annotation height do not match")
        self.assertEqual(channels, 3, "Image channel count is not equal to 3")

    def test_saveAnnotation(self) -> None:
        self.sample.unzip(ignoreCache = True)

        data = self.sample.load()
        height, width, _ = data.image.shape

        name = "UnitTestAnnotation"
        instances: List[CoretexSegmentationInstance] = []

        # Do not update width/height values to anything else except width/height of the image
        # otherwise test_sampleLoad will fail because it checks this data to be equal to actual image values
        result = self.sample.saveAnnotation(CoretexImageAnnotation.create(name, width, height, instances))
        self.assertTrue(result, "Failed to save annotation")

        self.sample.unzip(ignoreCache = True)

        data = self.sample.load()
        self.assertIsNotNone(data.annotation)

        # here only for mypy
        if data.annotation is None:
            raise ValueError

        self.assertEqual(data.annotation.name, name, "Annotation name does not match updated value")
        self.assertEqual(len(data.annotation.instances), len(instances), "Annotation instances do not match updated value")


if __name__ == "__main__":
    unittest.main()
