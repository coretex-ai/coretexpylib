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

from typing import Any, List, Optional, Union

from ..base_parameter import BaseParameter
from ....project import ProjectType


class FloatParameter(BaseParameter[Union[float, int]]):

    @property
    def types(self) -> List[type]:
        return [float, int]

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if isinstance(self.value, int):
            return float(self.value)

        return super().parseValue(type_)
