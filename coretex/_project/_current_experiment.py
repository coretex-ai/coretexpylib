from typing import Optional

from ..coretex import Experiment


class _CurrentExperimentContainer:

    experiment: Optional[Experiment] = None


def setCurrentExperiment(experiment: Optional[Experiment]) -> None:
    _CurrentExperimentContainer.experiment = experiment


def currentExperiment() -> Experiment:
    experiment = _CurrentExperimentContainer.experiment
    if experiment is None:
        raise ValueError("Experiment is not currently executing")

    return experiment
