from typing import Any, List, Optional, Union

from ..base_parameter import BaseParameter
from ....space import SpaceTask


class FloatParameter(BaseParameter[Union[float, int]]):

    @property
    def types(self) -> List[type]:
        return [float, int]

    def parseValue(self, task: SpaceTask) -> Optional[Any]:
        if isinstance(self.value, int):
            return float(self.value)

        return super().parseValue(task)
