from typing import Dict, Any

from .base_parameter import BaseParameter
from .parameter_type import ParameterType
from .parameters import *


def create(value: Dict[str, Any]) -> BaseParameter:
    dataType = value.get("data_type")
    if dataType is None:
        raise ValueError(f"\"data_type\" missing in {value}")

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

    if parameterType == ParameterType.imuVectors:
        return IMUVectorsParameter.decode(value)

    if parameterType == ParameterType.enum:
        return EnumParameter.decode(value)

    if parameterType == ParameterType.intList:
        return ListIntParameter.decode(value)

    if parameterType == ParameterType.floatList:
        return ListFloatParameter.decode(value)

    if parameterType == ParameterType.strList:
        return ListStrParameter.decode(value)

    if parameterType == ParameterType.enumList:
        return ListEnumParameter.decode(value)

    raise ValueError(f"Unknown parameter type \"{parameterType}\"")
