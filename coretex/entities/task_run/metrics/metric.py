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

from typing import Dict, List, Optional
from typing_extensions import Self

from .metric_type import MetricType
from ....codable import Codable, KeyDescriptor


class Metric(Codable):

    name: str
    xLabel: str
    xType: str
    yLabel: str
    yType: str
    xRange: Optional[List[float]]
    yRange: Optional[List[float]]

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["name"] = KeyDescriptor("metric")

        return descriptors

    @classmethod
    def create(
        cls,
        name: str,
        xLabel: str,
        xType: MetricType,
        yLabel: str,
        yType: MetricType,
        xRange: Optional[List[float]] = None,
        yRange: Optional[List[float]] = None
    ) -> Self:

        """
            name : str
                name of Metric
            xLabel : str
                label of x axis which will be displayed
            xType : MetricType
                type of x axis which will be displayed
            yLabel : str
                label of y axis which will be displayed
            yType : MetricType
                type of y axis which will be displayed
            xRange : Optional[List[float]]
                range in which values will be displayed for x axis
            yRange : Optional[List[float]]
                range in which values will be displayed for y axis
        """

        obj = cls()

        obj.name = name
        obj.xLabel = xLabel
        obj.xType = xType.name
        obj.yLabel = yLabel
        obj.yType = yType.name
        obj.xRange = xRange
        obj.yRange = yRange

        return obj

    def extract(self) -> Optional[float]:
        return None
