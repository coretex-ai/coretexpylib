from typing import List

from ..base_list_parameter import BaseListParameter


class ListIntParameter(BaseListParameter):

    @property
    def listTypes(self) -> List[type]:
        return [int]
