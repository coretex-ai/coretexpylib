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
from ..coretex import ExperimentStatus, NetworkDataset, Metric, ExperimentBuilder, Experiment
from ..logging import LogHandler, initializeLogger, LogSeverity
from ..networking import RequestFailedError
from ..folder_management import FolderManager


DatasetType = TypeVar("DatasetType", bound = "NetworkDataset")


class ExecutionType(IntEnum):
     # TODO: NYI on backend

     local = 1
     remote = 2


def _prepareForExecution(
     experimentId: int,
     datasetType: Optional[Type[DatasetType]] = None,
     metrics: Optional[List[Metric]] = None
) -> Experiment:

     experiment = ExperimentBuilder(experimentId).setDatasetType(datasetType).build()

     logPath = FolderManager.instance().logs / f"experiment_{experimentId}.log"
     customLogHandler = LogHandler.instance()
     customLogHandler.currentExperimentId = experiment.id

     # enable/disable verbose mode for experiments
     severity = LogSeverity.info
     verbose = experiment.parameters.get("verbose", False)

     if verbose:
          severity = LogSeverity.debug

     initializeLogger(severity, logPath)

     experiment.updateStatus(
          status = ExperimentStatus.inProgress,
          message = "Executing project."
     )

     if metrics is not None:
          experiment.createMetrics(metrics)
          logging.getLogger("coretexpylib").info(">> [Coretex] Metrics successfully created.")

     return experiment


def initializeProject(
     mainFunction: Callable[[Experiment], None],
     datasetType: Optional[Type[DatasetType]] = None,
     metrics: Optional[List[Metric]] = None,
     args: Optional[List[str]] = None
) -> None:

     """
          Initializes and starts the python project as
          Coretex experiment

          Parameters
          ----------
          mainFunction : Callable[[ExecutingExperiment], None]
               entry point function
          datasetType : Optional[Type[DatasetType]]
               Custom dataset if there is any (Not required)
          metrics : Optional[List[Metric]]
               list of metric objects that will be created for executing Experiment
          args : Optional[List[str]]
               list of command line arguments, if None sys.argv will be used
     """

     try:
          experimentId, callback = processRemote(args)
     except:
          experimentId, callback = processLocal(args)

     try:
          experiment = _prepareForExecution(experimentId, datasetType, metrics)

          callback.onStart()

          logging.getLogger("coretexpylib").info("Experiment execution started")
          mainFunction(experiment)

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
