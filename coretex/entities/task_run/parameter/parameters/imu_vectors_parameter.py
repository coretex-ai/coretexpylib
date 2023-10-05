from typing import Any, List, Dict, Optional

import json
import logging

from ..base_parameter import BaseParameter


class IMUVectorsParameter(BaseParameter[Dict[str, int]]):

    @property
    def types(self) -> List[type]:
        return [dict]

    def overrideValue(self, value: Optional[Any]) -> Optional[Any]:
        if value is None:
            return None

        try:
            parsedValue = json.loads(value.replace("'", "\""))
            return parsedValue
        except ValueError as e:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to override IMU vectors parameter \"{self.name}\". | {e}")
            return self.value
