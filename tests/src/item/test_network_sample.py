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

from typing import Optional

import unittest

from coretex import NetworkSample

from .base_network_sample_test import BaseNetworkSampleTest


class TestNetworkSample(BaseNetworkSampleTest.Base):

    sample: NetworkSample[None]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        sample: Optional[NetworkSample[None]] = NetworkSample.fetchById(55004)
        if sample is None:
            raise RuntimeError("Sample not found")

        cls.sample = sample

    # download test is located in the base class


if __name__ == "__main__":
    unittest.main()
