from typing import List

from ..base_list_parameter import BaseListParameter


class ListIntParameter(BaseListParameter[List[int]]):

    @property
    def listTypes(self) -> List[type]:
        return [int]
