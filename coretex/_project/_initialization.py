from typing import Callable, List

import logging
import sys

from ._remote import _processRemote
from ._local import _processLocal
from ._current_experiment import setCurrentExperiment
from .. import folder_manager
from ..coretex import Experiment, ExperimentStatus
from ..logging import LogHandler, LogSeverity, initializeLogger
from ..networking import RequestFailedError


def _prepareForExecution(experimentId: int) -> Experiment:
    experiment: Experiment = Experiment.fetchById(experimentId)

    customLogHandler = LogHandler.instance()
    customLogHandler.currentExperimentId = experiment.id

    # enable/disable verbose mode for experiments
    severity = LogSeverity.info
    verbose = experiment.parameters.get("verbose", False)

    if verbose:
        severity = LogSeverity.debug

    logPath = folder_manager.logs / f"experiment_{experimentId}.log"
    initializeLogger(severity, logPath)

    experiment.updateStatus(
        status = ExperimentStatus.inProgress,
        message = "Executing project."
    )

    return experiment


def initializeRProject(mainFunction: Callable[[Experiment], None], args: List[str]) -> None:
    """
        Initializes and starts the R project as Coretex experiment

        Parameters
        ----------
        mainFunction : Callable[[ExecutingExperiment], None]
            entry point function
        args : Optional[List[str]]
            list of command line arguments
    """

    try:
        experimentId, callback = _processRemote(args)
    except:
        experimentId, callback = _processLocal(args)

    try:
        experiment = _prepareForExecution(experimentId)
        setCurrentExperiment(experiment)

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
