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

from __future__ import annotations

from typing import Any, Type, List, Dict
from enum import IntEnum

import json

from .utils import getDatasetType, fetchDataset
from ..space import SpaceTask
from ...codable import Codable


class ExperimentParameterType(IntEnum):

    integer       = 1
    floatingPoint = 2
    string        = 3
    boolean       = 4
    dataset       = 5
    intList       = 6
    floatList     = 7
    strList       = 8
    imuVectors    = 9

    @staticmethod
    def fromStringValue(stringValue: str) -> ExperimentParameterType:
        for value in ExperimentParameterType:
            if value.stringValue == stringValue:
                return value

        raise ValueError(f">> [Coretex] Unknown parameter: {stringValue}")

    @property
    def stringValue(self) -> str:
        if self == ExperimentParameterType.integer:
            return "int"

        if self == ExperimentParameterType.floatingPoint:
            return "float"

        if self == ExperimentParameterType.string:
            return "str"

        if self == ExperimentParameterType.boolean:
            return "bool"

        if self == ExperimentParameterType.dataset:
            return "dataset"

        if self == ExperimentParameterType.intList:
            return "list[int]"

        if self == ExperimentParameterType.floatList:
            return "list[float]"

        if self == ExperimentParameterType.strList:
            return "list[str]"

        if self == ExperimentParameterType.imuVectors:
            return "IMUVectors"

        raise ValueError(f">> [Coretex] Unsupported type: {self}")

    @property
    def types(self) -> List[Type]:
        if self == ExperimentParameterType.integer:
            return [int]

        if self == ExperimentParameterType.floatingPoint:
            return [float, int]

        if self == ExperimentParameterType.string:
            return [str]

        if self == ExperimentParameterType.boolean:
            return [bool]

        if self == ExperimentParameterType.dataset:
            # parameters of type dataset have dataset ID as value
            # str is allowed to allow passing local paths to dataset
            return [int, str]

        if self == ExperimentParameterType.imuVectors:
            # parameters of type IMUVectors have dictionary as value
            return [dict]

        raise ValueError(f">> [Coretex] Unsupported type: {self}")

    @property
    def isList(self) -> bool:
        return self in [
            ExperimentParameterType.intList,
            ExperimentParameterType.floatList,
            ExperimentParameterType.strList
        ]

    @property
    def listType(self) -> Type:
        if not self.isList:
            raise ValueError(">> [Coretex] Type is not a list")

        if self == ExperimentParameterType.intList:
            return int

        if self == ExperimentParameterType.floatList:
            return float

        if self == ExperimentParameterType.strList:
            return str

        raise ValueError(f">> [Coretex] Unsupported type: {self}")


class ExperimentParameter(Codable):

    name: str
    description: str
    value: Any
    dataType: ExperimentParameterType
    required: bool

    def _encodeValue(self, key: str, value: Any) -> Any:
        if key == "dataType":
            if not isinstance(value, ExperimentParameterType):
                raise RuntimeError(f">> [Coretex] Unexpected error encoding parameter \"{key}\" with value \"{value}\"")

            return value.stringValue

        return super()._encodeValue(key, value)

    @classmethod
    def _decodeValue(cls, key: str, value: Any) -> Any:
        if key == "data_type":
            return ExperimentParameterType.fromStringValue(value)

        return super()._decodeValue(key, value)

    def isValid(self) -> bool:
        if not self.required and self.value is None:
            return True

        if self.dataType.isList:
            if not isinstance(self.value, list):
                return False

            return all(
                isinstance(element, self.dataType.listType)
                for element in self.value
            )

        # Dataset parameter is an integer under the hood, and in python bool is a subclass
        # of integer. To avoid assinging boolean values to dataset parameters we have to explicitly
        # check if the value which was passed in for dataset is a bool.
        if self.dataType == ExperimentParameterType.dataset and isinstance(self.value, bool):
            return False

        return any(isinstance(self.value, dataType) for dataType in self.dataType.types)

    def generateTypeDescription(self) -> str:
        if not self.dataType.isList or self.value is None:
            return type(self.value).__name__

        elementTypes = ", ".join({type(value).__name__ for value in self.value})
        return f"list[{elementTypes}]"

    @staticmethod
    def readExperimentConfig() -> List[ExperimentParameter]:
        parameters: List[ExperimentParameter] = []

        with open("./experiment.config", "rb") as configFile:
            configContent: Dict[str, Any] = json.load(configFile)
            parametersJson = configContent["parameters"]

            if not isinstance(parametersJson, list):
                raise ValueError(">> [Coretex] Invalid experiment.config file. Property 'parameters' must be an array")

            for parameterJson in parametersJson:
                parameter = ExperimentParameter.decode(parameterJson)
                if not parameter.isValid():
                    expected = parameter.dataType.stringValue
                    received = parameter.generateTypeDescription()

                    raise ValueError(f">> [Coretex] Parameter \"{parameter.name}\" has invalid type. Expected \"{expected}\", got \"{received}\"")

                parameters.append(parameter)

        return parameters


def parseParameters(parameters: List[ExperimentParameter], task: SpaceTask) -> Dict[str, Any]:
    values: Dict[str, Any] = {}

    for parameter in parameters:
        if parameter.dataType == ExperimentParameterType.floatingPoint and isinstance(parameter.value, int):
            values[parameter.name] = float(parameter.value)
        elif parameter.dataType == ExperimentParameterType.dataset:
            if parameter.value is None:
                values[parameter.name] = None
            else:
                isLocal = isinstance(parameter.value, str)
                datasetType = getDatasetType(task, isLocal)

                dataset = fetchDataset(datasetType, parameter.value)
                if dataset is None:
                    raise ValueError(f">> [Coretex] Failed to fetch dataset with ID: {parameter.value}")

                values[parameter.name] = dataset
        else:
            values[parameter.name] = parameter.value

    return values
