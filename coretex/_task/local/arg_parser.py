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

from typing import Optional, List, Any

from tap import Tap

from ...entities import BaseParameter, BaseListParameter, ParameterType


class LocalArgumentParser(Tap):

    username: Optional[str]
    password: Optional[str]

    projectId: int
    name: Optional[str]
    description: Optional[str]

    saveSnapshot: bool

    def __init__(self, parameters: List[BaseParameter]) -> None:
        self.parameters = parameters
        for parameter in parameters:
            # Dynamically add parameter names as attributes to the class, so they will
            # get parsed by parse_known_args
            setattr(self, parameter.name, None)

        super().__init__()

    def configure(self) -> None:
        self.add_argument("--username", nargs = "?", type = str, default = None)
        self.add_argument("--password", nargs = "?", type = str, default = None)

        self.add_argument("--projectId", type = int)
        self.add_argument("--name", nargs = "?", type = str, default = None)
        self.add_argument("--description", nargs = "?", type = str, default = None)

        self.add_argument("--saveSnapshot", action = 'store_const', const = True, default = False)

        for parameter in self.parameters:
            if parameter.dataType in [ParameterType.dataset, ParameterType.enum, ParameterType.enumList, ParameterType.imuVectors, ParameterType.range, ParameterType.boolean]:
                self.add_argument(f"--{parameter.name}", nargs = "?", type = parameter.overrideValue, default = None)
            elif isinstance(parameter, BaseListParameter):
                self.add_argument(f"--{parameter.name}", nargs = "+",  type = parameter.listTypes[0], default = None)
            else:
                self.add_argument(f"--{parameter.name}", nargs = "?", type = parameter.types[0], default = None)

    def getParameter(
        self,
        parameterName: str,
        default: Any
    ) -> Optional[Any]:

        parsedParameter = getattr(self, parameterName)
        if parsedParameter is None:
            return default

        return parsedParameter
