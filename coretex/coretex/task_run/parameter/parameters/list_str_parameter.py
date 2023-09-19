from typing import List

from ..base_list_parameter import BaseListParameter


class ListStrParameter(BaseListParameter[List[str]]):

    @property
    def listTypes(self) -> List[type]:
        return [str]
