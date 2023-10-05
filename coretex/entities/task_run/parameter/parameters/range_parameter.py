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

from typing import Any, List, Dict, Optional, Tuple

import logging

from ..base_parameter import BaseParameter
from ..utils import validateRangeStructure
from ....project import ProjectType


RANGE_LIMIT = 2^32


class RangeParameter(BaseParameter[Dict[str, int]]):

    @property
    def types(self) -> List[type]:
        return NotImplemented

    def validate(self) -> Tuple[bool, Optional[str]]:
        if not isinstance(self.value, dict):
            return False, None

        isValid, message = validateRangeStructure(self.name, self.value, self.required)
        if not isValid:
            return isValid, message

        if self.value["to"] > RANGE_LIMIT:
            return False, f"Range value \"to\" must not exceed 2^32"

        if not self.value["to"] > self.value["from"]:
            return False, f"Range value \"to\" must not be greater then \"from\""

        if not self.value["step"] <= self.value["to"] - self.value["from"]:
            return False, f"Range value \"step\" must be lower or equal to the distance between \"from\" and \"to\""

        return True, None

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return None

        return range(self.value["from"], self.value["to"], self.value["step"])

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        if value is None or self.value is None:
            return None

        try:
            args = value.split(" ")
            parsedValue: Dict[str, int] = {}

            # In case the only 2 values are entered, they will be treaded as "from" and "to"
            # Default step is 1
            if len(args) not in [2, 3]:
                return None

            parsedValue["from"] = int(args[0])
            parsedValue["to"] = int(args[1])
            parsedValue["step"] = int(args[2]) if len(args) == 3 else 1

            return parsedValue
        except ValueError as e:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to override range parameter \"{self.name}\". | {e}")
            return self.value
