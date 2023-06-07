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

from typing import Type, Optional, List

from .metric import Metric, MetricType
from .predefined_metrics import *


def getClassForMetric(name: str) -> Optional[Type[Metric]]:
    if name == "disk_read":
        return MetricDiskRead

    if name == "disk_write":
        return MetricDiskWrite

    if name == "cpu_usage":
        return MetricCPUUsage

    if name == "ram_usage":
        return MetricRAMUsage

    if name == "swap_usage":
        return MetricSwapUsage

    if name == "gpu_usage":
        return MetricGPUUsage

    if name == "gpu_temperature":
        return MetricGPUTemperature

    if name == "upload_speed":
        return MetricUploadSpeed

    if name == "download_speed":
        return MetricDownloadSpeed

    return None


def createMetric(
    name: str,
    xLabel: str,
    xType: MetricType,
    yLabel: str,
    yType: MetricType,
    xRange: Optional[List[float]] = None,
    yRange: Optional[List[float]] = None
) -> Metric:

    metric = getClassForMetric(name)
    if metric is None:
        raise ValueError(f"[Coretex] Failed to create {name} metric")

    return metric.create(name, xLabel, xType, yLabel, yType, xRange, yRange)
