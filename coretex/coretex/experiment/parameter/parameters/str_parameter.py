from typing import List

from ..base_parameter import BaseParameter


class StrParameter(BaseParameter):

    @property
    def types(self) -> List[type]:
        return [str]
