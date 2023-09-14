from typing import Optional, Tuple, List
from abc import abstractmethod

from .base_parameter import BaseParameter


class BaseListParameter(BaseParameter):

    @property
    def types(self) -> List[type]:
        return [list]

    @property
    @abstractmethod
    def listTypes(self) -> List[type]:
        pass

    @property
    def isList(self) -> bool:
        return True

    def validate(self) -> Tuple[bool, Optional[str]]:
        isValid, error = super().validate()
        if not isValid:
            return isValid, error

        if not self.required and self.value is None:
            return True, None

        # self.value is of type Optional[Any], but base class validate method already
        # checks if it is a list, if that fails this is not reachable
        for element in self.value:  # type: ignore[union-attr]
            if not any(isinstance(element, type_) for type_ in self.listTypes):
                return False, None

        return True, None
