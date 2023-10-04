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
            self.value = json.loads(value.replace("'", "\""))
            return self.value
        except ValueError:
            return None
