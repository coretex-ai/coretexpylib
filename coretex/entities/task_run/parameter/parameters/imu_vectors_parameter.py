from typing import List, Dict

from ..base_parameter import BaseParameter


class IMUVectorsParameter(BaseParameter[Dict[str, int]]):

    @property
    def types(self) -> List[type]:
        return [dict]
