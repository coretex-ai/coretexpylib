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

from typing import Optional, List, Dict, Any
from typing_extensions import Self
from pathlib import Path

import yaml

from ...entities import BaseParameter, parameter_factory
from ...codable import Codable, KeyDescriptor


TASK_CONFIG_PATH = Path(".", "task.yaml")


class ParamGroup(Codable):

    name: str
    params: Optional[List[BaseParameter]]

    @classmethod
    def _decodeValue(cls, key: str, value: Any) -> Any:
        if key == "params":
            return [parameter_factory.create(obj) for obj in value]

        return super()._decodeValue(key, value)


class TaskConfig(Codable):

    paramGroups: Optional[List[ParamGroup]]

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["paramGroups"] = KeyDescriptor("param_groups", ParamGroup, list)

        return descriptors

    @classmethod
    def decode(cls, params: dict) -> Self:
        if params.get("param_groups") is None:
            params["param_groups"] = []

        return super().decode(params)


def readTaskConfig() -> List[BaseParameter]:
    parameters: List[BaseParameter] = []

    if not TASK_CONFIG_PATH.exists():
        return []

    with TASK_CONFIG_PATH.open("r") as configFile:
        config = TaskConfig.decode(yaml.safe_load(configFile))

        if config.paramGroups is not None:
            for group in config.paramGroups:
                if group.params is not None:
                    parameters.extend(group.params)

    return parameters
