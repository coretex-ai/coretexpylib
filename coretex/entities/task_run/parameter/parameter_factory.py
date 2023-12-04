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

from .utils import getDatasetTypeByValueType
from .base_parameter import BaseParameter
from .parameter_type import ParameterType
from .parameters import *


def create(value: Dict[str, Any]) -> BaseParameter:
    dataType = value.get("data_type")
    dataValue = value.get("value")

    if dataType is None and dataValue is not None:
        dataType = getDatasetTypeByValueType(dataValue)

    elif dataType is None and dataValue is None:
        print('here???????/')
        dataType = 'str'

    print(f'dataType xD: {dataType}')

    if not isinstance(dataType, str):
        raise ValueError("\"data_type\" is not of type \"str\"")

    parameterType = ParameterType(dataType)

    if parameterType == ParameterType.integer:
        return IntParameter.decode(value)

    if parameterType == ParameterType.floatingPoint:
        return FloatParameter.decode(value)

    if parameterType == ParameterType.string:
        return StrParameter.decode(value)

    if parameterType == ParameterType.boolean:
        return BoolParameter.decode(value)

    if parameterType == ParameterType.dataset:
        return DatasetParameter.decode(value)

    if parameterType == ParameterType.model:
        return ModelParameter.decode(value)

    if parameterType == ParameterType.imuVectors:
        return IMUVectorsParameter.decode(value)

    if parameterType == ParameterType.enum:
        return EnumParameter.decode(value)

    if parameterType == ParameterType.range:
        return RangeParameter.decode(value)

    if parameterType == ParameterType.intList:
        return ListIntParameter.decode(value)

    if parameterType == ParameterType.floatList:
        return ListFloatParameter.decode(value)

    if parameterType == ParameterType.strList:
        return ListStrParameter.decode(value)

    if parameterType == ParameterType.datasetList:
        return ListDatasetParameter.decode(value)

    if parameterType == ParameterType.modelList:
        return ListModelParameter.decode(value)

    if parameterType == ParameterType.enumList:
        return ListEnumParameter.decode(value)

    raise ValueError(f"Unknown parameter type \"{parameterType}\"")
