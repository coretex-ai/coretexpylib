from typing import List, Optional, Any

import json

from ..base_list_parameter import BaseListParameter


class ListStrParameter(BaseListParameter[List[str]]):

    @property
    def listTypes(self) -> List[type]:
        return [str]
