from typing import List

from ..base_parameter import BaseParameter


class IntParameter(BaseParameter[int]):

    @property
    def types(self) -> List[type]:
        return [int]
