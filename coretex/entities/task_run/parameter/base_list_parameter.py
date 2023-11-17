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

from typing import Optional, Tuple, List, Generic
from abc import abstractmethod

from .base_parameter import BaseParameter, T


class BaseListParameter(BaseParameter[T], Generic[T]):

    @property
    def types(self) -> List[type]:
        return [list]

    @property
    @abstractmethod
    def listTypes(self) -> List[type]:
        pass

    def validate(self) -> Tuple[bool, Optional[str]]:
        isValid, error = super().validate()
        if not isValid:
            return isValid, error

        if not self.required and self.value is None:
            return True, None

        if self.required and len(self.value) == 0:  # type: ignore[arg-type]
            return False, f"Required parameter \"{self.name}\" must contain a non-empty array"

        # self.value is of type Optional[Any], but base class validate method already
        # checks if it is a list, if that fails this is not reachable
        for element in self.value:  # type: ignore[union-attr]

            # bool is a subclass of int, do not allow validation to pass if
            # we are looking for integer, but bool is received
            if isinstance(element, bool) and int in self.listTypes and not bool in self.listTypes:
                return False, None

            if not any(isinstance(element, type_) for type_ in self.listTypes):
                return False, None

        return True, None
