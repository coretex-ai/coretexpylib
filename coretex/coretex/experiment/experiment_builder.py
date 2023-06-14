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

from typing import Final, Optional, Type, Any
from typing_extensions import Self

import logging

from .experiment import Experiment
from ..space import SpaceTask
from ..dataset import *


class ExperimentBuilder:

    def __init__(self, experimentId: int) -> None:
        self.experimentId: Final = experimentId

        self.__datasetType: Optional[Type[Dataset]] = None

    def setDatasetType(self, datasetType: Optional[Type[Dataset]]) -> Self:
        self.__datasetType = datasetType
        return self

    def build(self) -> Experiment:
        experiment: Experiment = Experiment.fetchById(self.experimentId)

        if self.__datasetType is not None:
            for key, value in experiment.parameters.items():
                if isinstance(value, LocalDataset) and issubclass(self.__datasetType, LocalDataset):
                    experiment.parameters[key] = self.__datasetType(value.path)  # type: ignore

                if isinstance(value, NetworkDataset) and issubclass(self.__datasetType, NetworkDataset):
                    experiment.parameters[key] = self.__datasetType.fetchById(value.id)

        return experiment
