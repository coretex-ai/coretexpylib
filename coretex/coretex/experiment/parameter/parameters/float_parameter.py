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
