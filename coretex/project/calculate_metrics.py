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

from typing import Tuple, Dict
from multiprocessing.connection import Connection

import time

from ..coretex import MetricType
from ..networking import networkManager, NetworkRequestError
from ..coretex.experiment import Experiment
from ..coretex.experiment.metrics.metric_factory import createMetric


METRICS = [
    createMetric("cpu_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
    createMetric("ram_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
    createMetric("swap_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
    createMetric("download_speed", "time (s)", MetricType.interval, "bytes", MetricType.bytes),
    createMetric("upload_speed", "time (s)", MetricType.interval, "bytes", MetricType.bytes),
    createMetric("disk_read", "time (s)", MetricType.interval, "bytes", MetricType.bytes),
    createMetric("disk_write", "time (s)", MetricType.interval, "bytes", MetricType.bytes)
]


def sendSuccess(conn: Connection, message: str) -> None:
    conn.send({
        "code": 0,
        "message": message
    })


def sendFailure(conn: Connection, message: str) -> None:
    conn.send({
        "code": 1,
        "message": message
    })


def setupGPUMetrics() -> None:
    # Making sure that if GPU exists, GPU related metrics are added to METRICS list
    # py3nvml.nvmlShutdown() is never called because process for uploading metrics
    # will kill itself after experiment and in that moment py3nvml cleanup will
    # automatically be performed

    try:
        from py3nvml import py3nvml
        py3nvml.nvmlInit()

        METRICS.extend([
            createMetric("gpu_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
            createMetric("gpu_temperature", "time (s)", MetricType.interval, "usage (%)", MetricType.percent)
        ])
    except:
        pass


def uploadMetricsWorker(outputStream: Connection, refreshToken: str, experimentId: int) -> None:
    setupGPUMetrics()

    response = networkManager.authenticateWithRefreshToken(refreshToken)
    if response.hasFailed():
        sendFailure(outputStream, "Failed to authenticate with refresh token")
        return

    experiment = Experiment.fetchById(experimentId)
    if experiment is None:
        sendFailure(outputStream, f"Failed to fetch experiment with id: {experimentId}")
        return

    try:
        experiment.createMetrics(METRICS)
    except NetworkRequestError:
        sendFailure(outputStream, "Failed to create metrics")

    sendSuccess(outputStream, "Metrics worker succcessfully started")

    while True:
        startTime = time.time()
        metricValues: Dict[str, Tuple[float, float]] = {}

        for metric in experiment.metrics:
            metricValue = metric.extract()

            if metricValue is not None:
                metricValues[metric.name] = startTime, metricValue

        experiment.submitMetrics(metricValues)
        time.sleep(5)  # delay between sending generic metrics
