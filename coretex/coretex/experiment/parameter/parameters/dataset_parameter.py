from typing import Any, List, Optional

from ..base_parameter import BaseParameter
from ...utils import getDatasetType, fetchDataset
from ....space import SpaceTask


class DatasetParameter(BaseParameter):

    @property
    def types(self) -> List[type]:
        return [int, str]

    def parseValue(self, task: SpaceTask) -> Optional[Any]:
        if self.value is None:
            return None

        isLocal = isinstance(self.value, str)
        datasetType = getDatasetType(task, isLocal)

        dataset = fetchDataset(datasetType, self.value)
        if dataset is None:
            raise ValueError(f">> [Coretex] Failed to create dataset with type \"{datasetType.__name__}\"")

        return dataset
