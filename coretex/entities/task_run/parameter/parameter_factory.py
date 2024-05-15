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

from typing import Dict, Any

import inflection

from .utils import getValueParamType
from .base_parameter import BaseParameter
from .parameter_type import ParameterType
from .parameters import *
from ...secret import AWSSecret, GitSecret, CredentialsSecret


def cleanParamDict(value: Dict[str, Any]) -> Dict[str, Any]:
    if not "data_type" in value:
        value["data_type"] = None

    if not "value" in value:
        value["value"] = None

    if not "required" in value:
        value["required"] = False

    if not "description" in value:
        value["description"] = ""

    dataName: str = value["name"]
    dataType = value["data_type"]
    dataValue = value["value"]

    if dataType is None and dataValue is None:
        value["data_type"] = ParameterType.string.value

    if dataType is None and dataValue is not None:
        value["data_type"] = getValueParamType(dataValue, dataName).value

    return value

def create(value: Dict[str, Any]) -> BaseParameter:
    cleanParamDict(value)
    dataType = value.get("data_type")

    if not isinstance(dataType, str):
        raise ValueError("\"data_type\" is not of type \"str\"")

    # Convert snake_case keys into camelCase
    value = {
        inflection.camelize(key, uppercase_first_letter = False): value
        for key, value in value.items()
    }

    parameterType = ParameterType(dataType)

    if parameterType == ParameterType.integer:
        return IntParameter(**value)

    if parameterType == ParameterType.floatingPoint:
        return FloatParameter(**value)

    if parameterType == ParameterType.string:
        return StrParameter(**value)

    if parameterType == ParameterType.boolean:
        return BoolParameter(**value)

    if parameterType == ParameterType.dataset:
        return DatasetParameter(**value)

    if parameterType == ParameterType.model:
        return ModelParameter(**value)

    if parameterType == ParameterType.imuVectors:
        return IMUVectorsParameter(**value)

    if parameterType == ParameterType.enum:
        return EnumParameter(**value)

    if parameterType == ParameterType.range:
        return RangeParameter(**value)

    if parameterType == ParameterType.awsSecret:
        return SecretParameter(AWSSecret, **value)

    if parameterType == ParameterType.gitSecret:
        return SecretParameter(GitSecret, **value)

    if parameterType == ParameterType.credentialsSecret:
        return SecretParameter(CredentialsSecret, **value)

    if parameterType == ParameterType.intList:
        return ListIntParameter(**value)

    if parameterType == ParameterType.floatList:
        return ListFloatParameter(**value)

    if parameterType == ParameterType.strList:
        return ListStrParameter(**value)

    if parameterType == ParameterType.datasetList:
        return ListDatasetParameter(**value)

    if parameterType == ParameterType.modelList:
        return ListModelParameter(**value)

    if parameterType == ParameterType.enumList:
        return ListEnumParameter(**value)

    if parameterType == ParameterType.awsSecretList:
        return ListSecretParameter(AWSSecret, **value)

    if parameterType == ParameterType.gitSecretList:
        return ListSecretParameter(GitSecret, **value)

    if parameterType == ParameterType.credentialsSecretList:
        return ListSecretParameter(CredentialsSecret, **value)

    raise ValueError(f"Unknown parameter type \"{parameterType}\"")
