from typing import List

from ..base_parameter import BaseParameter


class BoolParameter(BaseParameter):

    @property
    def types(self) -> List[type]:
        return [bool]
