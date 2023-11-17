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

from ..base_parameter import BaseParameter
from ..utils import validateEnumStructure
from ....project import ProjectType


class EnumParameter(BaseParameter[Dict[str, Any]]):

    @property
    def types(self) -> List[type]:
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

        if not type(selected) is int:
            return False, f"Enum parameter \"{self.name}.selected\" has invalid type. Expected \"int\", got \"{type(selected).__name__}\""

        if selected >= len(options) or selected < 0:
            return False, f"Enum parameter \"{self.name}.selected\" has out of range value"

        return True, None

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return self.value

        selected: Optional[int] = self.value.get("selected")
        if selected is None:
            return None

        return self.value["options"][selected]

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        if value is None or self.value is None:
            return None

        try:
            parsedValue: Dict[str, Any] = self.value
            parsedValue["selected"] = int(value)
            return parsedValue
        except ValueError as e:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to override enum parameter \"{self.name}\". | {e}")
            return self.value
