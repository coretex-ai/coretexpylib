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

from typing import Optional, Type
from typing_extensions import Self
from types import TracebackType, FrameType
from multiprocessing.connection import Connection

import time
import timeit
import os
import logging
import multiprocessing
import signal

import psutil

from . import utils, metrics, artifacts
from ...entities import TaskRun
from ...networking import networkManager, NetworkRequestError


def _update(taskRun: TaskRun) -> None:
    logging.getLogger("coretexpylib").debug(">> [Coretex] Heartbeat")
    taskRun.updateStatus()  # updateStatus without params is considered heartbeat

    logging.getLogger("coretexpylib").debug(">> [Coretex] Uploading metrics")
    metrics.upload(taskRun)


def _taskRunWorker(output: Connection, refreshToken: str, taskRunId: int, parentId: int) -> None:
    isStopped = False

    def handleTerminateSignal(signum: int, frame: Optional[FrameType]) -> None:
        if signum != signal.SIGTERM:
            return

        logging.getLogger("coretexpylib").debug(">> [Coretex] Received terminate signal. Terminating...")

        nonlocal isStopped
        isStopped = True

    signal.signal(signal.SIGTERM, handleTerminateSignal)
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
        metrics.create(taskRun)
    except NetworkRequestError:
        utils.sendFailure(output, "Failed to create metrics")
        return

    utils.sendSuccess(output, "TaskRun worker succcessfully started")

    parent = psutil.Process(parentId)
    current = psutil.Process(os.getpid())

    # Start tracking files which are created inside current working directory
    with artifacts.track(taskRun):
        while parent.is_running() and not isStopped:
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Worker process id {current.pid}, parent process id {parent.pid}")

            # Measure elapsed time to calculate for how long should the process sleep
            start = timeit.default_timer()
            _update(taskRun)
            diff = timeit.default_timer() - start

            # Make sure that metrics and heartbeat are sent every 5 seconds
            if diff < 5:
                sleepTime = 5 - diff
                logging.getLogger("coretexpylib").debug(f">> [Coretex] Sleeping for {sleepTime}s")
                time.sleep(sleepTime)

    logging.getLogger("coretexpylib").debug(">> [Coretex] Finished")


class TaskRunWorker:

    def __init__(self, refreshToken: str, taskRunId: int) -> None:
        self._refreshToken = refreshToken

        output, input = multiprocessing.Pipe()
        self.__input = input

        self.__process = multiprocessing.Process(
            name = f"TaskRun {taskRunId} worker process",
            target = _taskRunWorker,
            args = (output, refreshToken, taskRunId, os.getpid()),
            daemon = True
        )

    def start(self) -> None:
        self.__process.start()

        result = self.__input.recv()
        if result["code"] != 0:
            raise RuntimeError(result["message"])

        message = result["message"]
        logging.getLogger("coretexpylib").info(f">> [Coretex] {message}")

    def stop(self) -> None:
        logging.getLogger("coretexpylib").info(">> [Coretex] Stopping the worker process")

        self.__process.terminate()
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

        if self.__process.is_alive():
            self.stop()

    def kill(self) -> None:
        logging.getLogger("coretexpylib").info(">> [Coretex] Killing the worker process")
        self.__process.kill()
