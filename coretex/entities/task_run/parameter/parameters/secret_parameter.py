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

from typing import Any, List, Optional, TypeVar, Type

import os

from ..parameter_type import ParameterType
from ..base_parameter import BaseParameter
from ....project import ProjectType
from ....secret import Secret


T = TypeVar("T", bound = Secret)


class SecretParameter(BaseParameter[str]):

    def __init__(
        self,
        secretType: Type[T],
        name: str,
        description: str,
        value: Optional[str],
        dataType: ParameterType,
        required: bool,
        type: int
    ) -> None:

        self._secretType = secretType

        super().__init__(name, description, value, dataType, required, type)

    @property
    def types(self) -> List[type]:
        return [str]

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return None

        if "CTX_NODE_ACCESS_TOKEN" in os.environ:
            return self._secretType.fetchNodeSecret(self.value, os.environ["CTX_NODE_ACCESS_TOKEN"])

        return self._secretType.fetchByName(self.value)
