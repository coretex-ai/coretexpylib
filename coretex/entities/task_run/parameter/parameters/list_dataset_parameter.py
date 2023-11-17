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

from ..base_list_parameter import BaseListParameter
from ...utils import getDatasetType, fetchDataset
from ....project import ProjectType
from ....dataset import Dataset


def _parseSingleDataset(value: Union[int, str], type_: ProjectType) -> Dataset:
    isLocal = isinstance(value, str)
    datasetType = getDatasetType(type_, isLocal)

    dataset = fetchDataset(datasetType, value)
    if dataset is None:
        raise ValueError(f">> [Coretex] Failed to create dataset with type \"{datasetType.__name__}\"")

    return dataset


class ListDatasetParameter(BaseListParameter[List[Union[int, str]]]):

    @property
    def listTypes(self) -> List[type]:
        return [int, str]

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return None

        return [
            _parseSingleDataset(datasetValue, type_)
            for datasetValue in self.value
        ]
