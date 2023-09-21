from typing import Any, List, Optional, Tuple, Dict

from ..base_parameter import BaseParameter
from ..utils import validateEnumStructure
from ....project import ProjectType


class EnumParameter(BaseParameter[Dict[str, Any]]):

    @property
    def types(self) -> List[type]:
        return NotImplemented

    def validate(self) -> Tuple[bool, Optional[str]]:
        isValid, message = validateEnumStructure(self.name, self.value, self.required)
        if not isValid:
            return isValid, message

        # validateEnumStructure already checks if value is of correct type
        value: Dict[str, Any] = self.value  # type: ignore[assignment]

        selected = value["selected"]
        options = value["options"]

        if selected is None and not self.required:
            return True, None

        if not type(selected) is int:
            return False, f"Enum parameter \"{self.name}.selected\" has invalid type. Expected \"int\", got \"{type(selected).__name__}\""

        if selected >= len(options) or selected < 0:
            return False, f"Enum parameter \"{self.name}.selected\" has out of range value"

        return True, None

    def parseValue(self, type_: ProjectType) -> Optional[Any]:
        if self.value is None:
            return self.value

        selected: Optional[int] = self.value.get("selected")
        if selected is None:
            return None

        return self.value["options"][selected]
