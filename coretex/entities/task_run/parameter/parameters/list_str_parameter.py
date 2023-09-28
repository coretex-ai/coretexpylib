from typing import List, Optional, Any

import json

from ..base_list_parameter import BaseListParameter


class ListStrParameter(BaseListParameter[List[str]]):

    @property
    def listTypes(self) -> List[type]:
        return [str]

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        if value is None:
            return None

        try:
            return json.loads(value.replace("'", "\""))
        except ValueError:
            return None
