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

from typing import Any, Type, List, Dict
from enum import IntEnum

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
    enum          = 10
    enumList      = 11

    @staticmethod
    def fromStringValue(stringValue: str) -> 'ExperimentParameterType':
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

        if self == ExperimentParameterType.enum:
            return "enum"

        if self == ExperimentParameterType.enumList:
            return "list[enum]"

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

        if self == ExperimentParameterType.enum:
            return [dict]

        if self == ExperimentParameterType.enumList:
            return [dict]

        raise ValueError(f">> [Coretex] Unsupported type: {self}")

    @property
    def isList(self) -> bool:
        return self in [
            ExperimentParameterType.intList,
            ExperimentParameterType.floatList,
            ExperimentParameterType.strList,
            ExperimentParameterType.enumList
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


class ParameterError(Exception):

    def __init__(self, message: str) -> None:
        super().__init__(f">> [Coretex] {message}")

    @staticmethod
    def type(parameter: 'ExperimentParameter') -> 'ParameterError':
        expected = parameter.dataType.stringValue
        received = parameter.generateTypeDescription()

        return ParameterError(f"Parameter \"{parameter.name}\" has invalid type. Expected \"{expected}\", got \"{received}\"")


def _validateGeneric(parameter: 'ExperimentParameter') -> None:
    if parameter.required and parameter.value is None:
        raise ParameterError.type(parameter)

    if not parameter.required and parameter.value is None:
        return

    if parameter.dataType.isList:
        if not isinstance(parameter.value, list):
            raise ParameterError.type(parameter)

        if not all(isinstance(element, parameter.dataType.listType) for element in parameter.value):
            raise ParameterError.type(parameter)
    else:
        # Dataset parameter is an integer under the hood, and in python bool is a subclass
        # of integer. To avoid assinging boolean values to dataset parameters we have to explicitly
        # check if the value which was passed in for dataset is a bool.
        if parameter.dataType == ExperimentParameterType.dataset and isinstance(parameter.value, bool):
            raise ParameterError.type(parameter)

        if not any(isinstance(parameter.value, dataType) for dataType in parameter.dataType.types):
            raise ParameterError.type(parameter)


def _validateEnumValue(parameter: 'ExperimentParameter') -> None:
    value = parameter.value

    # Enum parameter must be a dict
    if not isinstance(value, dict):
        raise ParameterError.type(parameter)

    # Enum parameter must contain 2 key-value pairs: selected and options
    if len(value) != 2 or "options" not in value or "selected" not in value:
        keys = ", ".join(value.keys())
        raise ParameterError(f"Enum parameter \"{parameter.name}\" must contain only \"selected\" and \"options\" properties, but it contains \"{keys}\"")

    options = value.get("options")

    # options must be an object of type list
    if not isinstance(options, list):
        raise ParameterError(f"Enum parameter \"{parameter.name}.options\" has invalid type. Expected \"list[str]\", got \"{type(options).__name__}\"")

    # all elements of options list must be strings
    if not all(isinstance(element, str) for element in options):
        elementTypes = ", ".join({type(element).__name__ for element in options})
        raise ParameterError(f"Elements of enum parameter \"{parameter.name}.options\" have invalid type. Expected \"list[str]\" got \"list[{elementTypes}]\"")

    # options elements must not be empty strings
    if not all(element != "" for element in options):
        raise ParameterError(f"Elements of enum parameter \"{parameter.name}.options\" must be non-empty strings.")

    selected = value.get("selected")

    if selected is None and parameter.required:
        raise ParameterError(f"Enum parameter \"{parameter.name}.selected\" has invalid type. Expected \"int\", got \"{type(selected).__name__}\"")

    if selected is None and not parameter.required:
        return

    if parameter.dataType.isList:
        if not isinstance(selected, list):
            raise ParameterError(f"Enum list parameter \"{parameter.name}.selected\" has invalid type. Expected \"list[int]\", got \"{type(selected).__name__}\"")

        if not all(isinstance(element, int) for element in selected):
            elementTypes = ", ".join({type(element).__name__ for element in selected})
            raise ParameterError(f"Enum list parameter \"{parameter.name}.selected\" has invalid type. Expected \"list[int]\", got \"list[{elementTypes}]\"")

        invalidIndxCount = len([element for element in selected if element >= len(options) or element < 0])
        if invalidIndxCount > 0:
            raise ParameterError(f"Enum list parameter \"{parameter.name}.selected\" has out of range values")
    else:
        if not isinstance(selected, int):
            raise ParameterError(f"Enum parameter \"{parameter.name}.selected\" has invalid type. Expected \"int\", got \"{type(selected).__name__}\"")

        if selected >= len(options) or selected < 0:
            raise ParameterError(f"Enum parameter \"{parameter.name}.selected\" has out of range value")


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

    def onDecode(self) -> None:
        super().onDecode()

        self.__validate()

    def __validate(self) -> None:
        if self.dataType == ExperimentParameterType.enum or self.dataType == ExperimentParameterType.enumList:
            _validateEnumValue(self)
        else:
            _validateGeneric(self)

    def generateTypeDescription(self) -> str:
        if not self.dataType.isList or self.value is None:
            return type(self.value).__name__

        elementTypes = ", ".join({type(value).__name__ for value in self.value})
        return f"list[{elementTypes}]"


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
        elif parameter.dataType == ExperimentParameterType.enum:
            values[parameter.name] = parameter.value["options"][parameter.value["selected"]]
        else:
            values[parameter.name] = parameter.value

    return values
