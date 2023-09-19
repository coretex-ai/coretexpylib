from typing import Any, List, Optional, Union

from ..base_parameter import BaseParameter
from ...utils import getDatasetType, fetchDataset
from ....project import ProjectType


class DatasetParameter(BaseParameter[Union[int, str]]):

    @property
    def types(self) -> List[type]:
        return [int, str]

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return None

        isLocal = isinstance(self.value, str)
        datasetType = getDatasetType(type_, isLocal)

        dataset = fetchDataset(datasetType, self.value)
        if dataset is None:
            raise ValueError(f">> [Coretex] Failed to create dataset with type \"{datasetType.__name__}\"")

        return dataset
