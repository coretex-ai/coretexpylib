#     Copyright (C) 2023  BioMech LLC

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

from __future__ import annotations

from typing import Final, Optional, Type, TypeVar, Generic

import os
import logging

from .parameters import ExperimentParameter, ExperimentParameterType
from .experiment import Experiment
from ..space import SpaceTask
from ..dataset import NetworkDataset, CustomDataset, ImageSegmentationDataset, ComputerVisionDataset


class ExperimentBuilder:

    def __init__(self, experimentId: int) -> None:
        self.experimentId: Final = experimentId

        self.__datasetType: Optional[Type[NetworkDataset]] = None

    def setDatasetType(self, datasetType: Optional[Type[NetworkDataset]]) -> ExperimentBuilder:
        self.__datasetType = datasetType
        return self

    def __getDatasetType(self, experiment: ExecutingExperiment) -> Type[NetworkDataset]:
        if self.__datasetType is not None:
            return self.__datasetType

        if experiment.spaceTask == SpaceTask.other:
            return CustomDataset

        if experiment.spaceTask == SpaceTask.imageSegmentation:
            return ImageSegmentationDataset

        if experiment.spaceTask == SpaceTask.computerVision:
            return ComputerVisionDataset

        logging.getLogger("coretexpylib").debug(f">> [Coretex] SpaceTask ({experiment.spaceTask}) does not have a dataset type using CustomDataset")

        # Returning CustomDataset in case the spaceTask doesn't have it's dataset type
        return CustomDataset

    def __loadExperimentConfig(self, experiment: ExecutingExperiment) -> None:
        parameters = ExperimentParameter.readExperimentConfig()

        for parameter in parameters:
            if parameter.dataType == ExperimentParameterType.floatingPoint and isinstance(parameter.value, int):
                experiment.parameters[parameter.name] = float(parameter.value)

            if parameter.dataType == ExperimentParameterType.dataset:
                if parameter.value is None:
                    experiment.parameters[parameter.name] = None
                else:
                    dataset = self.__getDatasetType(experiment).fetchById(parameter.value)

                    if dataset is None:
                        raise ValueError(f">> [Coretex] Failed to fetch dataset with ID: {parameter.value}")

                    experiment.parameters[parameter.name] = dataset

    def build(self) -> ExecutingExperiment:
        experiment: Optional[ExecutingExperiment[NetworkDataset]] = ExecutingExperiment.fetchById(self.experimentId)
        if experiment is None:
            raise Exception(f">> [Coretex] Experiment (ID: {self.experimentId}) not found")

        if not os.path.exists("experiment.config"):
            raise FileNotFoundError(">> [Coretex] (experiment.config) file not found")

        self.__loadExperimentConfig(experiment)

        return experiment


DatasetType = TypeVar("DatasetType", bound = "NetworkDataset")


class ExecutingExperiment(Experiment, Generic[DatasetType]):

    """
        Represents the instance of the currently executing Experiment on Coretex.ai

        Example
        -------
        >>> from coretex import ExecutingExperiment
        \b
        >>> experiment: ExecutingExperiment[DatasetType] = ExecutingExperiment.current()
        >>> print(experiment.id)
        1023
    """

    __currentExperiment: Optional[ExecutingExperiment] = None

    @staticmethod
    def current() -> ExecutingExperiment:
        """
            Returns
            -------
            ExecutingExperiment -> currently executing Experiment instance
        """

        if ExecutingExperiment.__currentExperiment is None:
            raise ValueError(">> [Coretex] Tried to access current experiment, but no experiment is executing")

        return ExecutingExperiment.__currentExperiment

    @staticmethod
    def startExecuting(experimentId: int, datasetType: Optional[Type[NetworkDataset]] = None) -> ExecutingExperiment:
        if ExecutingExperiment.__currentExperiment is not None:
            raise ValueError(">> [Coretex] Tried to set current experiment, but current experiment is already set")

        ExecutingExperiment.__currentExperiment = ExperimentBuilder(experimentId).setDatasetType(datasetType).build()
        return ExecutingExperiment.current()

    @staticmethod
    def stopExecuting() -> None:
        if ExecutingExperiment.__currentExperiment is None:
            raise ValueError(">> [Coretex] Tried to deallocate current experiment, but current experiment is already deallocated")

        ExecutingExperiment.__currentExperiment = None

    @property
    def dataset(self) -> DatasetType:
        """
            If there is no parameter with name "dataset" calling this will raise an exception

            Returns
            -------
            Dataset object if there was a parameter with name "dataset" entered when the experiment was started
        """
        return self.parameters["dataset"]  # type: ignore
