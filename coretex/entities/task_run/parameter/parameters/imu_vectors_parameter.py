from typing import Any, List, Dict, Optional

import json

from ..base_parameter import BaseParameter


class IMUVectorsParameter(BaseParameter[Dict[str, int]]):

    @property
    def types(self) -> List[type]:
        return [dict]

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        if value is None:
            return None

        try:
            return json.loads(value.replace("'", "\""))
        except ValueError:
            return None
