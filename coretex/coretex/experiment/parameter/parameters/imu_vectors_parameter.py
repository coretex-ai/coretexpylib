from typing import List

from ..base_parameter import BaseParameter


class IMUVectorsParameter(BaseParameter):

    @property
    def types(self) -> List[type]:
        return [dict]
