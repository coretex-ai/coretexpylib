from typing import Any, List, Optional, Union

from ..base_list_parameter import BaseListParameter
from ....project import ProjectType


class ListFloatParameter(BaseListParameter[List[Union[float, int]]]):

    @property
    def listTypes(self) -> List[type]:
        return [float, int]

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return None

        values: List[float] = []

        for element in self.value:
            if isinstance(element, int):
                values.append(float(element))
            else:
                values.append(element)

        return values
