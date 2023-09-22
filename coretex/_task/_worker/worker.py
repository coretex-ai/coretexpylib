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

from typing import Tuple, Dict, Optional, Type, List
from typing_extensions import Self
from types import TracebackType
from multiprocessing.connection import Connection

import time
import timeit
import os
import logging
import multiprocessing

import psutil

from . import utils
from ...entities import MetricType, TaskRun, Metric
from ...networking import networkManager, NetworkRequestError
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
        py3nvml.nvmlInit()

        metrics.extend([
            metric_factory.createMetric("gpu_usage", "time (s)", MetricType.interval, "usage (%)", MetricType.percent, None, [0, 100]),
            metric_factory.createMetric("gpu_temperature", "time (s)", MetricType.interval, "usage (%)", MetricType.percent)
        ])

        logging.getLogger("coretexpylib").debug(">> [Coretex] Initialized GPU metrics")
        py3nvml.nvmlShutdown()
    except:
        logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to initialize GPU metrics")

    return metrics


def _heartbeat(taskRun: TaskRun) -> None:
    # Update status without parameters is considered run hearbeat
    taskRun.updateStatus()


def _uploadMetrics(taskRun: TaskRun) -> None:
    x = time.time()
    metricValues: Dict[str, Tuple[float, float]] = {}

    for metric in taskRun.metrics:
        metricValue = metric.extract()

        if metricValue is not None:
            metricValues[metric.name] = x, metricValue

    taskRun.submitMetrics(metricValues)


def _taskRunWorker(output: Connection, refreshToken: str, taskRunId: int) -> None:
    utils.initializeLogger(taskRunId)

    response = networkManager.authenticateWithRefreshToken(refreshToken)
    if response.hasFailed():
        utils.sendFailure(output, "Failed to authenticate with refresh token")
        return

    try:
        taskRun: TaskRun = TaskRun.fetchById(taskRunId)
    except NetworkRequestError:
        utils.sendFailure(output, f"Failed to fetch TaskRun with id \"{taskRunId}\"")
        return

    try:
        taskRun.createMetrics(_getMetrics())
    except NetworkRequestError:
        utils.sendFailure(output, "Failed to create metrics")
        return

    utils.sendSuccess(output, "TaskRun worker succcessfully started")

    currentProcess = psutil.Process(os.getpid())
    while (parent := currentProcess.parent()) is not None:
        logging.getLogger("coretexpylib").debug(f">> [Coretex] Worker process id {currentProcess.pid}, parent process id {parent.pid}")

        # If parent process ID is set to 1 then that means that the parent process has terminated
        # the process (this is only true for Unix-based systems), but since we run the Node
        # from the docker container which uses Linux as a base then it is safe to use.
        #
        # In docker container the pid of the Node process is 1, but we are safe to chech since the
        # node should never be a parent of this process for metric upload, only the TaskRun
        # process can be the parent.
        if parent.pid == 1 or not parent.is_running() or not utils.isAlive(output):
            logging.getLogger("coretexpylib").debug(">> [Coretex] Terminating worker process...")
            break

        # Measure elapsed time to calculate for how long should the process sleep
        start = timeit.default_timer()
        logging.getLogger("coretexpylib").debug(">> [Coretex] Heartbeat")
        _heartbeat(taskRun)

        logging.getLogger("coretexpylib").debug(">> [Coretex] Uploading metrics")
        _uploadMetrics(taskRun)
        diff = timeit.default_timer() - start

        # Make sure that metrics and heartbeat are sent every 5 seconds
        if diff < 5:
            sleepTime = 5 - diff
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Sleeping for {sleepTime}s")
            time.sleep(sleepTime)


class TaskRunWorker:

    def __init__(self, refreshToken: str, taskRunId: int) -> None:
        self._refreshToken = refreshToken

        self.__outputStream, self.__inputStream = multiprocessing.Pipe()

        self.__process = multiprocessing.Process(
            name = f"TaskRun {taskRunId} worker process",
            target = _taskRunWorker,
            args = (self.__outputStream, refreshToken, taskRunId),
            daemon = True
        )

    def start(self) -> None:
        self.__process.start()

        result = self.__inputStream.recv()
        if result["code"] != 0:
            raise RuntimeError(result["message"])

        logging.getLogger("coretexpylib").info(result["message"])

    def stop(self) -> None:
        self.__process.kill()
        self.__process.join()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exceptionType: Optional[Type[BaseException]],
        exceptionValue: Optional[BaseException],
        exceptionTraceback: Optional[TracebackType]
    ) -> None:

        self.stop()
