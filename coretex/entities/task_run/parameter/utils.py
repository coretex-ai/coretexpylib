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

from typing import Optional, Any, Tuple, Dict, List

from .base_parameter import ParameterType


def validateEnumStructure(name: str, value: Optional[Any], required: bool) -> Tuple[bool, Optional[str]]:
    if not isinstance(value, dict):
        return False, None

    # Enum parameter must contain 2 key-value pairs: selected and options
    if len(value) != 2 or "options" not in value or "selected" not in value:
        keys = ", ".join(value.keys())
        return False, f"Enum parameter \"{name}\" must contain only \"selected\" and \"options\" properties, but it contains \"{keys}\""

    options = value.get("options")

    # options must be an object of type list
    if not isinstance(options, list):
        return False, f"Enum parameter \"{name}.options\" has invalid type. Expected \"list[str]\", got \"{type(options).__name__}\""

    # all elements of options list must be strings
    if not all(isinstance(element, str) for element in options):
        elementTypes = ", ".join({type(element).__name__ for element in options})
        return False, f"Elements of enum parameter \"{name}.options\" have invalid type. Expected \"list[str]\" got \"list[{elementTypes}]\""

    # options elements must not be empty strings
    if not all(element != "" for element in options):
        return False, f"Elements of enum parameter \"{name}.options\" must be non-empty strings."

    selected = value.get("selected")
    if selected is None and required:
        return False, f"Enum parameter \"{name}.selected\" has invalid type. Expected \"int\", got \"{type(selected).__name__}\""

    return True, None


def validateRangeStructure(name: str, value: Dict[str, Any], required: bool) -> Tuple[bool, Optional[str]]:
    if len(value) != 3 or "from" not in value or "to" not in value or "step" not in value:
        keys = ", ".join(value.keys())
        return False, f"Range parameter \"{name}\" must contain only \"from\",  \"to\" and \"step\" properties, but it contains \"{keys}\""

    if any(element is None for element in value.values()) and required:
        return False, f"Elements of range parameter \"{name}\" must not be null"

    if not all(type(element) is int for element in value.values()) and required:
        elementTypes = ", ".join({type(element).__name__ for element in value.values()})
        return False, f"Elements of range parameter \"{name}\" have invalid type. Expected \"int\" got \"{elementTypes}\""

    if any(type(element) is float for element in value.values()):
        return False, "Range parameter does not support float values"

    return True, None

def getValueParamType(value: Any, name: str) -> ParameterType:
    if isinstance(value, bool):
        return ParameterType.boolean

    if isinstance(value, int):
        return ParameterType.integer

    if isinstance(value, float):
        return ParameterType.floatingPoint

    if isinstance(value, str):
        return ParameterType.string

    if isinstance(value, list):
        return getListParamType(value, name)

    supportedTypes = [type_.name for type_ in ParameterType]

    raise ValueError(f">> [Coretex] Parameter \"{name}\" has invalid type. Expected \"{supportedTypes}\", got \"{type(value)}\".")

def getListParamType(value: List[Any], name: str) -> ParameterType:
    if all(isinstance(item, int) for item in value):
        return ParameterType.intList

    if all(isinstance(item, float) for item in value):
        return ParameterType.floatList

    if all(isinstance(item, str) for item in value):
        return ParameterType.strList

    typesFound = ", ".join([type(item).__name__ for item in value])
    raise ValueError(f">> [Coretex] Parameter \"{name}\" cannot contain multiple value type: \"{typesFound}\".")
