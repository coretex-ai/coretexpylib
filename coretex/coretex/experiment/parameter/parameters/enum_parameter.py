from typing import Any, List, Optional, Tuple, Dict

from ..base_parameter import BaseParameter
from ..utils import validateEnumStructure
from ....space import SpaceTask


class EnumParameter(BaseParameter):

    @property
    def types(self) -> List[type]:
        return [str]

    def validate(self) -> Tuple[bool, Optional[str]]:
        isValid, message = validateEnumStructure(self.name, self.value, self.required)
        if not isValid:
            return isValid, message

        # validateEnumStructure already checks if value is of correct type
        value: Dict[str, Any] = self.value  # type: ignore[assignment]

        selected = value["selected"]
        options = value["options"]

        if not isinstance(selected, int):
            return False, f"Enum parameter \"{self.name}.selected\" has invalid type. Expected \"int\", got \"{type(selected).__name__}\""

        if selected >= len(options) or selected < 0:
            return False, f"Enum parameter \"{self.name}.selected\" has out of range value"

        return True, None

    def parseValue(self, task: SpaceTask) -> Optional[Any]:
        if self.value is None:
            return self.value

        return self.value["options"][self.value["selected"]]
