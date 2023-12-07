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

from typing import Dict, Optional, Any, Tuple, List, TypeVar, Generic
from abc import ABC, abstractmethod

import logging

from .parameter_type import ParameterType
from .utils import getValueParamType
from ...project import ProjectType
from ....codable import Codable, KeyDescriptor


T = TypeVar("T")


class BaseParameter(ABC, Codable, Generic[T]):

    name: str
    description: str
    value: Optional[T]
    dataType: ParameterType
    required: bool

    @property
    @abstractmethod
    def types(self) -> List[type]:
        pass

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["dataType"] = KeyDescriptor("data_type", ParameterType)

        return descriptors

    def makeExceptionMessage(self) -> str:
        expected = self.dataType.value
        received = self.generateTypeDescription()

        return f"Parameter \"{self.name}\" has invalid type. Expected \"{expected}\", got \"{received}\""

    def validate(self) -> Tuple[bool, Optional[str]]:
        if not self.required and self.value is None:
            return True, None

        # bool is a subclass of int, do not allow validation to pass if
        # we are looking for integer, but bool is received
        if isinstance(self.value, bool) and int in self.types and not bool in self.types:
            return False, None

        if not any(isinstance(self.value, dataType) for dataType in self.types):
            return False, None

        return True, None

    def generateTypeDescription(self) -> str:
        if not isinstance(self.value, list) or self.value is None:
            return type(self.value).__name__

        elementTypes = ", ".join({type(value).__name__ for value in self.value})
        return f"list[{elementTypes}]"

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        return self.value

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        return value


def validateParameters(parameters: List[BaseParameter], verbose: bool = True) -> Dict[str, Any]:
    parameterValidationResults: Dict[str, bool] = {}

    for parameter in parameters:
        isValid, message = parameter.validate()
        if not isValid:
            if message is None:
                message = parameter.makeExceptionMessage()

            if verbose:
                logging.getLogger("coretexpylib").fatal(f">> [Coretex] {message}")

        parameterValidationResults[parameter.name] = isValid

    return parameterValidationResults
