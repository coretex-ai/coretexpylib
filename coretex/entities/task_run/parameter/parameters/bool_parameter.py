from typing import List

from ..base_parameter import BaseParameter


class BoolParameter(BaseParameter[bool]):

    @property
    def types(self) -> List[type]:
        return [bool]
