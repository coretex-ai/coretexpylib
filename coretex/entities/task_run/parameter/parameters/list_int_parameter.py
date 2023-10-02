from typing import List, Optional, Any

import json

from ..base_list_parameter import BaseListParameter


class ListIntParameter(BaseListParameter[List[int]]):

    @property
    def listTypes(self) -> List[type]:
        return [int]
