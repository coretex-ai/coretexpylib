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

from typing import List, Optional, Any

import logging

from ..base_parameter import BaseParameter


class BoolParameter(BaseParameter[bool]):

    @property
    def types(self) -> List[type]:
        return [bool]

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        if value is None:
            return None

        try:
            if value.lower() == "true":
                return True

            if value.lower() == "false":
                return False

            raise ValueError("Could not recognise parsed value as boolean. Only accepted options are \"true\" and \"false\" (case insensitive)")
        except ValueError as e:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to override boolean parameter \"{self.name}\". | {e}")
            return self.value
