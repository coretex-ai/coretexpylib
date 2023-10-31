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

from typing import Tuple, Dict, List

import time
import logging

from ...entities import MetricType, TaskRun, Metric
from ...entities.task_run.metrics import metric_factory


def _getMetrics() -> List[Metric]:
    metrics = [
        metric_factory.createMetric("cpu_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
        metric_factory.createMetric("ram_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
        metric_factory.createMetric("swap_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
        metric_factory.createMetric("download_speed", "time (s)", MetricType.interval, "bytes", MetricType.bytes),
        metric_factory.createMetric("upload_speed", "time (s)", MetricType.interval, "bytes", MetricType.bytes),
        metric_factory.createMetric("disk_read", "time (s)", MetricType.interval, "bytes", MetricType.bytes),
        metric_factory.createMetric("disk_write", "time (s)", MetricType.interval, "bytes", MetricType.bytes)
    ]

    # If GPU exists add GPU related metrics to the list
    try:
        from py3nvml import py3nvml

        # Do not shutdown otherwise when extracting gpu metrics it will throw error
        py3nvml.nvmlInit()

        metrics.extend([
            metric_factory.createMetric("gpu_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
            metric_factory.createMetric("gpu_temperature", "time (s)", MetricType.interval, "usage (%)", MetricType.percent)
        ])

        logging.getLogger("coretexpylib").debug(">> [Coretex] Initialized GPU metrics")
    except:
        logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to initialize GPU metrics")

    return metrics


def create(taskRun: TaskRun) -> None:
    taskRun.createMetrics(_getMetrics())


def upload(taskRun: TaskRun) -> None:
    x = time.time()
    metricValues: Dict[str, Tuple[float, float]] = {}

    for metric in taskRun.metrics:
        metricValue = metric.extract()

        if metricValue is not None:
            metricValues[metric.name] = x, metricValue

    taskRun.submitMetrics(metricValues)
