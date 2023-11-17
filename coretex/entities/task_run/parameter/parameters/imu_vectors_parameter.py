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

from typing import Any, List, Dict, Optional

import json
import logging

from ..base_parameter import BaseParameter


class IMUVectorsParameter(BaseParameter[Dict[str, int]]):

    @property
    def types(self) -> List[type]:
        return [dict]

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        if value is None:
            return None

        try:
            parsedValue = json.loads(value.replace("'", "\""))
            return parsedValue
        except ValueError as e:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to override IMU vectors parameter \"{self.name}\". | {e}")
            return self.value
