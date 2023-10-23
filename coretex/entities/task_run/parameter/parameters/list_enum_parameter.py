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

from typing import Any, List, Optional, Tuple, Dict

import logging

from ..base_list_parameter import BaseListParameter
from ..utils import validateEnumStructure
from ....project import ProjectType


class ListEnumParameter(BaseListParameter[Dict[str, Any]]):

    @property
    def types(self) -> List[type]:
        return NotImplemented

    @property
    def listTypes(self) -> List[type]:
        return NotImplemented

    def validate(self) -> Tuple[bool, Optional[str]]:
        isValid, message = validateEnumStructure(self.name, self.value, self.required)
        if not isValid:
            return isValid, message

        # validateEnumStructure already checks if value is of correct type
        value: Dict[str, Any] = self.value  # type: ignore[assignment]

        selected = value["selected"]
        options = value["options"]

        if selected is None and not self.required:
            return True, None

        if not isinstance(selected, list):
            return False, f"Enum list parameter \"{self.name}.selected\" has invalid type. Expected \"list[int]\", got \"{type(selected).__name__}\""

        if not all(type(element) is int for element in selected):
            elementTypes = ", ".join({type(element).__name__ for element in selected})
            return False, f"Enum list parameter \"{self.name}.selected\" has invalid type. Expected \"list[int]\", got \"list[{elementTypes}]\""

        invalidIndxCount = len([element for element in selected if element >= len(options) or element < 0])
        if invalidIndxCount > 0:
            return False, f"Enum list parameter \"{self.name}.selected\" has out of range values"

        return True, None

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return self.value

        selected: Optional[List[int]] = self.value["selected"]
        options: List[str] = self.value["options"]

        if selected is None:
            return None

        return [options[value] for value in selected]

    def overrideValue(self, values: Optional[Any]) -> Optional[Any]:
        if values is None or self.value is None:
            return None

        try:
            parsedValue: Dict[str, Any] = self.value
            parsedValue["selected"] = []

            for value in values.split(" "):
                parsedValue["selected"].append(int(value))

            return parsedValue
        except ValueError as e:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to override list[enum] parameter \"{self.name}\". | {e}")
            return self.value
