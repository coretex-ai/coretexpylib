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

from abc import abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from typing_extensions import Self

from .metric_type import MetricType
from ....codable import Codable, KeyDescriptor
from ....networking import networkManager, RequestType


class Metric(Codable):

    name: str
    xLabel: str
    xType: str
    yLabel: str
    yType: str

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["name"] = KeyDescriptor("metric")

        return descriptors

    @classmethod
    def create(cls, name: str, xLabel: str, xType: MetricType, yLabel: str, yType: MetricType) -> Self:
        obj = cls()

        obj.name = name
        obj.xLabel = xLabel
        obj.xType = xType.name
        obj.yLabel = yLabel
        obj.yType = yType.name

        return obj

    @classmethod
    def createMetrics(cls, experimentId: int, values: List[Tuple[str, str, MetricType, str, MetricType]]) -> bool:
        metrics: List[Metric] = []

        for value in values:
            metrics.append(cls.create(*value))

        parameters: Dict[str, Any] = {
            "experiment_id": experimentId,
            "metrics": [metric.encode() for metric in metrics]
        }

        endpoint = "model-queue/metrics-meta"
        response = networkManager.genericJSONRequest(
            endpoint = endpoint,
            requestType = RequestType.post,
            parameters = parameters
        )

        return not response.hasFailed()

    def extract(self) -> Optional[float]:
        return None
