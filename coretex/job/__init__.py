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

from typing import Callable, Optional, Type, TypeVar, List
from enum import IntEnum

import logging
import sys

from .remote import processRemote
from .local import processLocal
from .. import folder_manager
from ..coretex import RunStatus, NetworkDataset, Metric, RunBuilder, Run
from ..logging import LogHandler, initializeLogger, LogSeverity
from ..networking import RequestFailedError


DatasetType = TypeVar("DatasetType", bound = "NetworkDataset")


class ExecutionType(IntEnum):
     # TODO: NYI on backend

     local = 1
     remote = 2


def _prepareForExecution(
     runId: int,
     datasetType: Optional[Type[DatasetType]] = None,
     metrics: Optional[List[Metric]] = None
) -> Run:

     run = RunBuilder(runId).setDatasetType(datasetType).build()

     logPath = folder_manager.logs / f"run_{runId}.log"
     customLogHandler = LogHandler.instance()
     customLogHandler.currentRunId = run.id

     # enable/disable verbose mode for runs
     severity = LogSeverity.info
     verbose = run.parameters.get("verbose", False)

     if verbose:
          severity = LogSeverity.debug

     initializeLogger(severity, logPath)

     run.updateStatus(
          status = RunStatus.inProgress,
          message = "Executing job."
     )

     if metrics is not None:
          run.createMetrics(metrics)
          logging.getLogger("coretexpylib").info(">> [Coretex] Metrics successfully created.")

     return run


def initializeJob(
     mainFunction: Callable[[Run], None],
     datasetType: Optional[Type[DatasetType]] = None,
     metrics: Optional[List[Metric]] = None,
     args: Optional[List[str]] = None
) -> None:

     """
          Initializes and starts the python job as
          Coretex run

          Parameters
          ----------
          mainFunction : Callable[[ExecutingRun], None]
               entry point function
          datasetType : Optional[Type[DatasetType]]
               Custom dataset if there is any (Not required)
          metrics : Optional[List[Metric]]
               list of metric objects that will be created for executing Run
          args : Optional[List[str]]
               list of command line arguments, if None sys.argv will be used
     """

     try:
          runId, callback = processRemote(args)
     except:
          runId, callback = processLocal(args)

     try:
          run = _prepareForExecution(runId, datasetType, metrics)

          callback.onStart()

          logging.getLogger("coretexpylib").info("Run execution started")
          mainFunction(run)

          callback.onSuccess()
     except RequestFailedError:
          callback.onNetworkConnectionLost()
     except KeyboardInterrupt:
          callback.onKeyboardInterrupt()
     except BaseException as ex:
          callback.onException(ex)

          # sys.exit is ok here, finally block is guaranteed to execute
          # due to how sys.exit is implemented (it internally raises SystemExit exception)
          sys.exit(1)
     finally:
          callback.onCleanUp()
