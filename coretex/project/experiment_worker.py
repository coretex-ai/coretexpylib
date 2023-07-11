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
import os
import logging

import psutil

from ..coretex import MetricType, Experiment
from ..networking import networkManager, NetworkRequestError
from ..logging import initializeLogger, LogSeverity
from ..folder_management import FolderManager
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

        logging.getLogger("coretexpylib").debug(">> [Coretex] Initialized GPU metrics")
    except:
        logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to initialize GPU metrics")


def _isAlive(output: Connection) -> bool:
    try:
        # If parent process gets killed with SIGKILL there
        # is no guarantee that the child process will get
        # closed so we ping the parent process to check if
        # the pipe is available or not
        output.send(None)
    except BrokenPipeError:
        output.close()
        return False

    return output.writable and not output.closed


def _heartbeat(experiment: Experiment) -> None:
    # Update status without parameters is considered experiment hearbeat
    experiment.updateStatus()


def _uploadMetrics(experiment: Experiment) -> None:
    x = time.time()
    metricValues: Dict[str, Tuple[float, float]] = {}

    for metric in experiment.metrics:
        metricValue = metric.extract()

        if metricValue is not None:
            metricValues[metric.name] = x, metricValue

    experiment.submitMetrics(metricValues)


def experimentWorker(output: Connection, refreshToken: str, experimentId: int) -> None:
    workerLogPath = FolderManager.instance().logs / f"experiment_worker_{experimentId}.log"
    initializeLogger(LogSeverity.debug, workerLogPath)

    currentProcess = psutil.Process(os.getpid())

    setupGPUMetrics()

    response = networkManager.authenticateWithRefreshToken(refreshToken)
    if response.hasFailed():
        sendFailure(output, "Failed to authenticate with refresh token")
        return

    try:
        experiment: Experiment = Experiment.fetchById(experimentId)
    except NetworkRequestError:
        sendFailure(output, f"Failed to fetch experiment with id \"{experimentId}\"")
        return

    try:
        experiment.createMetrics(METRICS)
    except NetworkRequestError:
        sendFailure(output, "Failed to create metrics")

    sendSuccess(output, "Experiment worker succcessfully started")

    while (parent := currentProcess.parent()) is not None:
        logging.getLogger("coretexpylib").debug(f">> [Coretex] Worker process id {currentProcess.pid}, parent process id {parent.pid}...")

        # If parent process ID is set to 1 then that means that the parent process has terminated
        # the process (this is only true for Unix-based systems), but since we run the Node
        # from the docker container which uses Linux as a base then it is safe to use.
        #
        # In docker container the pid of the Node process is 1, but we are safe to chech since the
        # node should never be a parent of this process for metric upload, only the experiment
        # process can be the parent.
        if parent.pid == 1 or not parent.is_running() or not _isAlive(output):
            logging.getLogger("coretexpylib").debug(">> [Coretex] Terminating worker process...")
            break

        logging.getLogger("coretexpylib").debug(">> [Coretex] Heartbeat")
        _heartbeat(experiment)

        logging.getLogger("coretexpylib").debug(">> [Coretex] Uploading metrics")
        _uploadMetrics(experiment)

        logging.getLogger("coretexpylib").debug(">> [Coretex] Sleeping for 5s")
        time.sleep(5)  # delay between sending generic metrics
